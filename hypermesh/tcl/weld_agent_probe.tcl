namespace eval ::weldagent {}

proc ::weldagent::json_escape {value} {
    return [string map [list "\\" "\\\\" "\"" "\\\"" "\n" "\\n" "\r" "\\r" "\t" "\\t"] $value]
}

proc ::weldagent::command_available {name} {
    return [expr {[llength [info commands $name]] > 0 ? "true" : "false"}]
}

proc ::weldagent::run_probe {output_path} {
    *clearmark components 1
    *createmarkpanel components 1 "Select exactly two Components for Weld Agent"
    set component_ids [hm_getmark components 1]
    if {[llength $component_ids] != 2} {
        error "Weld Agent requires exactly two Components; selected [llength $component_ids]"
    }

    set component_json {}
    foreach component_id $component_ids {
        set component_name [hm_getvalue components id=$component_id dataname=name]
        lappend component_json [format {    {"id": %d, "name": "%s"}} $component_id [::weldagent::json_escape $component_name]]
    }

    set normalized_output [file normalize $output_path]
    file mkdir [file dirname $normalized_output]
    set stream [open $normalized_output w]
    fconfigure $stream -encoding utf-8 -translation lf
    puts $stream "{"
    puts $stream {  "schema_version": "1.0",}
    puts $stream {  "selected_components": [}
    puts $stream [join $component_json ",\n"]
    puts $stream {  ],}
    puts $stream "  \"capabilities\": {"
    puts $stream [format {    "geomexport": %s,} [::weldagent::command_available *geomexport]]
    puts $stream [format {    "legacy_geomoutputdata": %s,} [::weldagent::command_available *geomoutputdata]]
    puts $stream [format {    "connector_create": %s} [::weldagent::command_available *CE_ConnectorCreate]]
    puts $stream "  }"
    puts $stream "}"
    close $stream
    return $normalized_output
}
