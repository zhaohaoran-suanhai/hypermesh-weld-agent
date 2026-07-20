namespace eval ::weldagent {}

proc ::weldagent::json_escape {value} {
    return [string map [list "\\" "\\\\" "\"" "\\\"" "\n" "\\n" "\r" "\\r" "\t" "\\t"] $value]
}

proc ::weldagent::json_number_array {values} {
    return "\[[join $values {, }]\]"
}

proc ::weldagent::component_summary {component_id} {
    *clearmark surfaces 1
    *createmark surfaces 1 "by comp id" $component_id
    set surface_count [hm_marklength surfaces 1]
    if {$surface_count == 0} {
        error "EMPTY_COMPONENT_GEOMETRY: Component $component_id has no surfaces"
    }
    set bbox [hm_getboundingbox surfaces 1 1 0 0]
    if {[llength $bbox] != 6} {
        error "EMPTY_COMPONENT_GEOMETRY: Component $component_id has no valid surface bounding box"
    }

    *clearmark solids 1
    *createmark solids 1 "by comp id" $component_id
    set solid_count [hm_marklength solids 1]

    *clearmark elements 1
    *createmark elements 1 "by comp id" $component_id
    set element_count [hm_marklength elements 1]

    return [list $surface_count $solid_count $element_count $bbox]
}

proc ::weldagent::set_visible_components {component_ids} {
    *displaycollectorwithfilter components "none" "" 1 0
    if {[llength $component_ids] > 0} {
        *clearmark components 2
        eval *createmark components 2 $component_ids
        *displaycollectorsbymark components 2 on 1 0
    }
}

proc ::weldagent::export_component_step {component_id step_path} {
    ::weldagent::set_visible_components [list $component_id]
    set options [list \
        "Version=AP214" \
        "LayerMode=None" \
        "Export=Displayed" \
        "Units=Millimeters" \
        "GeometryMode=Standard" \
        "TopologyMode=Solid/Shell" \
        "AssemblyMode=Hierarchy" \
        "WriteNameFrom=Component" \
        "OptimizeForCAD=Off"]
    set export_status [catch {
        *geomexport "step_ct" $step_path $options
    } export_message]
    if {$export_status != 0} {
        error "EXPORT_FAILED: Component $component_id: $export_message"
    }
    if {![file isfile $step_path] || [file size $step_path] <= 0} {
        error "EXPORT_FAILED: missing or empty STEP for Component $component_id"
    }
}

proc ::weldagent::component_record_json {record} {
    lassign $record component_id name step_path summary
    lassign $summary surface_count solid_count element_count bbox
    return [format {    {
      "id": %d,
      "name": "%s",
      "step_path": "%s",
      "summary": {
        "surface_count": %d,
        "solid_count": %d,
        "element_count": %d,
        "bbox": %s
      }
    }} $component_id \
        [::weldagent::json_escape $name] \
        [::weldagent::json_escape $step_path] \
        $surface_count \
        $solid_count \
        $element_count \
        [::weldagent::json_number_array $bbox]]
}

proc ::weldagent::write_export_manifest {run_dir run_id component_records} {
    set model_file [hm_info currentfile]
    set warnings_json ""
    if {$model_file eq ""} {
        set model_name "Untitled"
        set warnings_json {"HyperMesh model has not been saved; model_name is Untitled"}
    } else {
        set model_name [file rootname [file tail $model_file]]
    }
    set build [hm_info -appinfo DISPLAYVERSION]
    set component_json {}
    foreach record $component_records {
        lappend component_json [::weldagent::component_record_json $record]
    }

    set target [file join $run_dir "export-manifest.json"]
    set temporary "$target.tmp"
    set stream [open $temporary w]
    fconfigure $stream -encoding utf-8 -translation lf
    set write_status [catch {
        puts $stream "\{"
        puts $stream {  "schema_version": "1.0",}
        puts $stream [format {  "run_id": "%s",} [::weldagent::json_escape $run_id]]
        puts $stream "  \"hypermesh\": \{"
        puts $stream [format {    "build": "%s",} [::weldagent::json_escape $build]]
        puts $stream [format {    "model_name": "%s",} [::weldagent::json_escape $model_name]]
        puts $stream {    "units": "mm",}
        puts $stream {    "coordinate_system": "global"}
        puts $stream "  \},"
        puts $stream "  \"export_options\": \{"
        puts $stream {    "cad_type": "step_ct",}
        puts $stream {    "version": "AP214",}
        puts $stream {    "units": "Millimeters",}
        puts $stream {    "export": "Displayed",}
        puts $stream {    "layer_mode": "None",}
        puts $stream {    "geometry_mode": "Standard",}
        puts $stream {    "topology_mode": "Solid/Shell",}
        puts $stream {    "assembly_mode": "Hierarchy",}
        puts $stream {    "write_name_from": "Component",}
        puts $stream {    "optimize_for_cad": "Off"}
        puts $stream "  \},"
        puts $stream {  "components": [}
        puts $stream [join $component_json ",\n"]
        puts $stream {  ],}
        puts $stream [format {  "warnings": [%s]} $warnings_json]
        puts $stream "\}"
    } write_message write_options]
    set close_status [catch {close $stream} close_message]
    if {$write_status != 0 || $close_status != 0} {
        if {[file isfile $temporary]} {
            file delete -force $temporary
        }
        if {$write_status != 0} {
            return -options $write_options $write_message
        }
        error $close_message
    }
    file rename $temporary $target
    return [file normalize $target]
}

proc ::weldagent::run_export_probe {output_root} {
    *clearmark components 1
    *createmarkpanel components 1 "Select exactly two Components for Weld Agent STEP export"
    set selected_ids [hm_getmark components 1]
    if {[llength $selected_ids] != 2 || [lindex $selected_ids 0] == [lindex $selected_ids 1]} {
        error "INVALID_SELECTION: select exactly two distinct Components"
    }

    *clearmark components 2
    *createmark components 2 displayed
    set original_visible [hm_getmark components 2]

    set run_id "hm-[clock format [clock seconds] -format %Y%m%d-%H%M%S]-[pid]"
    set run_dir [file normalize [file join $output_root $run_id]]
    if {[file exists $run_dir]} {
        error "OUTPUT_CONFLICT: run directory already exists: $run_dir"
    }
    file mkdir $run_dir

    set created_steps {}
    set status [catch {
        set component_records {}
        foreach component_id $selected_ids {
            set name [hm_getvalue components id=$component_id dataname=name]
            set summary [::weldagent::component_summary $component_id]
            set step_path [file normalize [file join $run_dir "component-$component_id.step"]]
            lappend created_steps $step_path
            ::weldagent::export_component_step $component_id $step_path
            lappend component_records [list $component_id $name $step_path $summary]
        }
        set manifest_path [::weldagent::write_export_manifest \
            $run_dir \
            $run_id \
            $component_records]
    } message options]

    set restore_status [catch {
        ::weldagent::set_visible_components $original_visible
    } restore_message]
    if {$status != 0 || $restore_status != 0} {
        foreach step_path $created_steps {
            if {[file isfile $step_path]} {
                file delete -force $step_path
            }
        }
        foreach artifact [list \
            [file join $run_dir "export-manifest.json"] \
            [file join $run_dir "export-manifest.json.tmp"]] {
            if {[file isfile $artifact]} {
                file delete -force $artifact
            }
        }
        if {$restore_status == 0} {
            return -options $options $message
        }
        error "DISPLAY_RESTORE_FAILED: $restore_message"
    }
    return $manifest_path
}
