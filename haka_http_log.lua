-- Loading dissectors
require('protocol/ipv4')
require('protocol/tcp')
require('protocol/http')
local tcp_connection = require("protocol/tcp_connection")
local http = require('protocol/http')

-- Add your HTTP ports here
http.install_tcp_rule(80)
http.install_tcp_rule(3128)
http.install_tcp_rule(8080)

-- Process HTTP responses
haka.rule{
    hook = http.events.response,
    eval = function (http, response)
        local event = {}
        local ref
        local timestamp
        if response.headers["Date"] then
            local pattern = "%a+, (%d+) (%a+) (%d+) (%d+):(%d+):(%d+) (%a+)"
            local s = response.headers["Date"] -- Mon, 03 Sep 2012 15:31:30 GMT
            local day,month,year,hour,min,sec,tz=s:match(pattern)
            timestamp = day .. "/" .. month .. "/" .. year .. ":" .. hour .. ":" .. min .. ":" .. sec .. " +0000"
        else
            timestamp = "1/Jan/1970:00:00:00 +0000"
        end
        table.insert(event, tostring(http.flow.srcip))
        table.insert(event, " - - [" .. timestamp .. "] ")
        table.insert(event, "\"")
        table.insert(event, http.request.method)
        table.insert(event, " ")
        table.insert(event, http.request.uri)
        table.insert(event, " HTTP/")
        table.insert(event, http.request.version)
        table.insert(event, "\" ")
        table.insert(event, response.status)
        table.insert(event, " ")
        -- Print a default request size... (to be fixed)
        table.insert(event, "10")
        if http.request.headers["referer"] == nil then
            ref = " \"-\" "
        else
            ref = "\"" .. http.request.headers["referer"] .. "\" "
        end
        table.insert(event, ref)
        table.insert(event, "\"")
        table.insert(event, http.request.headers["User-Agent"])
        table.insert(event, "\"")
        table.insert(event, "\n")
        print(table.concat(event))
    end
}