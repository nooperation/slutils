// Server data
string URL_REGISTER = "http://x:5000/server/register/";
string URL_UPDATE =   "http://x:5000/server/update/";
string URL_CONFIRM =  "http://x:5000/server/";

integer SERVER_CUSTOM_HTTP_REQUEST = -1001;
integer SERVER_REGISTRATION_REQUEST = -1002;

integer SCRIPT_REGISTRATION_RESPONSE = -2002;
integer SCRIPT_CUSTOM_HTTP_RESPONSE = -10000000;

list handler_map;
integer handler_map_length = 0;
integer HANDLER_MAP_STRIDE = 2;

string kResultTag = "result";
string kMessageTag = "message";
string kResultSuccess = "success";
string kResultError = "error";

string serverType = "Population Server";
key registerRequestId;
key updateRequestId;
key urlRequestId;
key listenKey;
string assignedUrl = "";

string CONFIG_PATH = "Config";
integer currentConfigLine = 0;
key configQueryId = NULL_KEY;
string authToken = "";
string expectedAuthToken = "";
key confirmRequestId = NULL_KEY;
string shard = "Unknown";

OnGetCapabilities(key request_id)
{
    list capabilities = [];
    integer i = 0;
    for(i = 0; i < handler_map_length; i += HANDLER_MAP_STRIDE)
    {
        capabilities += llList2Integer(handler_map, i + 1);
    }

    string capabilities_json = llList2Json(JSON_ARRAY, capabilities);
    llHTTPResponse(request_id, 200, capabilities_json);
}

UpdateServer()
{
    Output("Updating server...");
    updateRequestId = llHTTPRequest(URL_UPDATE, [HTTP_METHOD, "POST", HTTP_MIMETYPE,"application/x-www-form-urlencoded"],
        "address=" +  llEscapeURL(assignedUrl) +
        "&private_token=" + authToken);
}

integer GetHandlerID(string name)
{
    integer i = 0;
    for(i = 0; i < handler_map_length; i += HANDLER_MAP_STRIDE)
    {
        string handler_name = llList2String(handler_map, i);
        if(handler_name == name)
        {
            return llList2Integer(handler_map, i + 1);
        }
    }

    return 0;
}

integer ProcessRequest(list path_parts, key requestId)
{
    string firstPathPart = llList2String(path_parts, 0);

    if(firstPathPart == "Base")
    {
        string secondPathPart = llList2String(path_parts, 1);

        if(secondPathPart == "GetCapabilities")
        {
            OnGetCapabilities(requestId);
            return TRUE;
        }
        else if(secondPathPart == "Reset")
        {
            llHTTPResponse(requestId, 200, "OK.");
            llSleep(1.0);
            llResetScript();
            return TRUE;
        }
        else if(secondPathPart == "Confirm")
        {
            llHTTPResponse(requestId, 200, "OK.");
            return TRUE;
        }
        else if(secondPathPart == "InitComplete")
        {
            llHTTPResponse(requestId, 200, "OK.");
            state StartServer;
        }
    }
    else
    {
        integer handler_id = GetHandlerID(firstPathPart);
        if(handler_id == 0)
        {
            return FALSE;
        }

        llMessageLinked(LINK_THIS, handler_id, llDumpList2String(path_parts, ","), requestId);
        return TRUE;
    }

    return FALSE;
}

Output(string message)
{
    llOwnerSay(message);
}

string ExtractValueFromQuery(string query, string name)
{
    list queryParts = llParseString2List(query, ["&"], []);
    integer numQueryParts = llGetListLength(queryParts);
    integer i;

    for(i = 0; i < numQueryParts; i++)
    {
        list keyValuePair = llParseString2List(llList2String(queryParts, i), ["="], []);
        if(llGetListLength(keyValuePair) == 2)
        {
            if(llList2String(keyValuePair, 0) == name)
            {
                return llList2String(keyValuePair, 1);
            }
        }
    }

    return "";
}

/// <summary>
/// Processes a single line from the settings file
/// Each line must be in the format of: setting name = value
/// </summary>
/// <param name="line">Raw line from settnigs file</param>
processTriggerLine(string line)
{
    integer seperatorIndex = llSubStringIndex(line, "=");
    string name;
    string value;

    if(seperatorIndex <= 0)
    {
        Output("Missing separator: " + line);
        return;
    }

    name = llToLower(llStringTrim(llGetSubString(line, 0, seperatorIndex - 1), STRING_TRIM_TAIL));
    value = llStringTrim(llGetSubString(line, seperatorIndex + 1, -1), STRING_TRIM);

    if(name == "authtoken")
    {
        authToken = value;
    }
    else if(name == "shard")
    {
        shard = value;
    }
}

/// <summary>
/// Handles processing of a single line of our actions file.
/// </summary>
/// <param name="line">Line from actions notecard</param>
processConfigLine(string line)
{
    line = llStringTrim(line, STRING_TRIM_HEAD);

    if(line == "" || llGetSubString(line, 0, 0) == "#")
    {
        return;
    }

    processTriggerLine(line);
}

integer ReadConfig()
{
    authToken = "";

    if(llGetInventoryType(CONFIG_PATH) != INVENTORY_NONE)
    {
        if(llGetInventoryKey(CONFIG_PATH) != NULL_KEY)
        {
            Output("Reading config...");
            currentConfigLine = 0;
            configQueryId = llGetNotecardLine(CONFIG_PATH, currentConfigLine);
            return TRUE;
        }
        else
        {
            if(authToken != "")
            {
                Output("Config file has no key (Never saved? Not full-perm?). You must add the following line to the Config notecard:\nauthtoken=" + authToken);
            }
            else
            {
                Output("Config file has no key (Never saved? Not full-perm?)");
            }
        }
    }

    return FALSE;
}

default
{
    state_entry()
    {
        Output("Fresh state");

        if(!ReadConfig())
        {
            state StartServer;
        }
    }

    dataserver(key queryId, string data)
    {
        if(queryId == configQueryId)
        {
            if(data == EOF)
            {
                state StartServer;
            }

            processConfigLine(data);
            configQueryId = llGetNotecardLine(CONFIG_PATH, ++currentConfigLine);
        }
    }

    on_rez(integer start_param)
    {
        llResetScript();
    }

    changed(integer change)
    {
        if(change & (CHANGED_OWNER | CHANGED_REGION | CHANGED_REGION_START))
        {
            Output("Resetting...");
            llResetScript();
        }
    }
}

state StartServer
{
    state_entry()
    {
        llSetColor(<1, 0, 0>, ALL_SIDES);
        Output("Server starting...");
        urlRequestId = llRequestSecureURL();
    }

    http_request(key requestId, string method, string body)
    {
        if(requestId != urlRequestId)
        {
            return;
        }

        if(method == URL_REQUEST_GRANTED)
        {
            assignedUrl = body;

            Output("Got URL: " + assignedUrl);

            if(authToken == "")
            {
                Output("Registering server...");
                vector pos = llGetPos();
                registerRequestId = llHTTPRequest(URL_REGISTER, [HTTP_METHOD, "POST",HTTP_MIMETYPE,"application/x-www-form-urlencoded"],
                    "shard=" + llEscapeURL(shard) +
                    "&region=" + llEscapeURL(llGetRegionName()) +
                    "&owner_name=" + llEscapeURL(llGetUsername(llGetOwner())) +
                    "&owner_key=" + (string)llGetOwner() +
                    "&object_key=" + (string)llGetKey() +
                    "&address=" +  llEscapeURL(assignedUrl) +
                    "&object_name=" + llEscapeURL(llGetObjectName()) +
                    "&x=" + (string)llRound(pos.x) +
                    "&y=" + (string)llRound(pos.y) +
                    "&z=" + (string)llRound(pos.z));
            }
            else
            {
                UpdateServer();
            }
        }
        else if(method == URL_REQUEST_DENIED)
        {
            Output("Failed to acquire URL!");
        }
    }

    http_response(key requestId, integer status, list metadata, string body)
    {
        if (requestId == registerRequestId)
        {
            integer successful = FALSE;

            if(status == 200)
            {
                string result = llJsonGetValue(body, [kResultTag]);
                string message = llJsonGetValue(body, [kMessageTag]);

                if(result == kResultSuccess)
                {
                    Output("Registered!");
                    authToken = message;
                    Output("Base server registered. Now to configure it...");
                    state InitializeServer;
                }
                else if(result == kResultError)
                {
                    Output("Failed to register server: " + message);
                }
                else
                {
                    Output("Invalid response while registering server: " + body);
                }

                return;
            }
            else
            {
                Output("Failed to register due to http status " + (string)status + ": " + body);
                return;
            }
        }
        else if(requestId == updateRequestId)
        {
            if(status == 200)
            {
                string result = llJsonGetValue(body, [kResultTag]);
                string message = llJsonGetValue(body, [kMessageTag]);

                if(result == kResultSuccess)
                {
                    Output("Updated!");
                    state ServerRunning;
                }
                else if(result == kResultError)
                {
                    Output("Failed to update server: " + message);
                }
                else
                {
                    Output("Invalid response while updating server: " + body);
                }

                return;
            }
        }
        else
        {
            Output("Unknown request");
        }
    }

    on_rez(integer start_param)
    {
        llResetScript();
    }

    changed(integer change)
    {
        if(change & (CHANGED_OWNER | CHANGED_REGION | CHANGED_REGION_START))
        {
            Output("Resetting...");
            llResetScript();
        }
        if(change & CHANGED_INVENTORY)
        {
            Output("Resetting...");
            llResetScript();
        }
    }
}


state InitializeServer
{
    state_entry()
    {
        llSetColor(<1, 1, 0>, ALL_SIDES);
        Output("Looking for config...");

        expectedAuthToken = authToken;
        authToken = "";

        if(!ReadConfig())
        {
            Output("Please create a notecard named 'Config' with the following contents and add it to this object's inventory:\nauthtoken=" + expectedAuthToken);
        }
    }

    on_rez(integer start_param)
    {
        llResetScript();
    }

    touch(integer num_detected)
    {
        if(llDetectedKey(0) != llGetOwner())
        {
            return;
        }

        ReadConfig();
    }

    changed(integer change)
    {
        if(change & (CHANGED_OWNER | CHANGED_REGION | CHANGED_REGION_START))
        {
            Output("Resetting...");
            llResetScript();
        }
        else if(change & CHANGED_INVENTORY)
        {
            ReadConfig();
        }
    }

    http_request(key requestId, string method, string body)
    {
        // TODO: This is duplicate code....
        string requestedPathRaw = ExtractValueFromQuery(llGetHTTPHeader(requestId, "x-query-string"), "path");
        list requestedPathParts = llParseString2List(requestedPathRaw, ["/"], []);
        integer numRequestedPathParts = llGetListLength(requestedPathParts);

        if(numRequestedPathParts == 0)
        {
            llHTTPResponse(requestId, 400, "Bad Request");
            return;
        }

        if(!ProcessRequest(requestedPathParts, requestId))
        {
            llHTTPResponse(requestId, 501, "Not Implemented");
        }
    }

    dataserver(key queryId, string data)
    {
        if(queryId == configQueryId)
        {
            if(data == EOF)
            {
                Output("Unexpected end of line. You must add the following line to the Config notecard:\nauthtoken=" + expectedAuthToken);
                return;
            }

            processConfigLine(data);

            if(authToken != "" && authToken != expectedAuthToken)
            {
                Output("Unexpected auth token. You must add the following line to the Config notecard:\nauthtoken=" + expectedAuthToken);
                authToken = "";
            }
            else if(authToken == expectedAuthToken)
            {
                Output("Config file valid. Visit the following URL to complete initialization:\n" + URL_CONFIRM + authToken + "/confirm/");
            }
            else
            {
                configQueryId = llGetNotecardLine(CONFIG_PATH, ++currentConfigLine);
            }
        }
    }
}

state ServerRunning
{
    state_entry()
    {
        Output("Server running...");

        llSetColor(<0, 1, 0>, ALL_SIDES);
        handler_map = [];
        handler_map_length = 0;

        llMessageLinked(LINK_THIS, SERVER_REGISTRATION_REQUEST, "", NULL_KEY);
    }

    http_request(key requestId, string method, string body)
    {
        string requestedPathRaw = ExtractValueFromQuery(llGetHTTPHeader(requestId, "x-query-string"), "path");
        list requestedPathParts = llParseString2List(requestedPathRaw, ["/"], []);
        integer numRequestedPathParts = llGetListLength(requestedPathParts);

        if(numRequestedPathParts == 0)
        {
            llHTTPResponse(requestId, 400, "Bad Request");
            return;
        }

        if(!ProcessRequest(requestedPathParts, requestId))
        {
            llHTTPResponse(requestId, 501, "Not Implemented");
        }
    }

    link_message(integer sender_num, integer source, string body, key id)
    {
        if(source == SCRIPT_REGISTRATION_RESPONSE)
        {
            integer id = (integer)((string)id);
            if(id <= 0)
            {
                llOwnerSay("Invalid key specified: " + (string)id);
            }
            else
            {
                integer existing_key = GetHandlerID(body);
                if(existing_key > 0)
                {
                    llOwnerSay("Duplicate key detected: " + body);
                }
                else
                {
                    llOwnerSay("Added handler for /" + body + "");
                    handler_map += [body, (integer)id];
                    handler_map_length += 2;
                }
            }
        }
        else if(source <= SCRIPT_CUSTOM_HTTP_RESPONSE)
        {
            integer status = source - SCRIPT_CUSTOM_HTTP_RESPONSE;
            llHTTPResponse(id, status, body);
        }
    }

    on_rez(integer start_param)
    {
        llResetScript();    
    }
    
    changed(integer change)
    {
        if(change & (CHANGED_OWNER | CHANGED_REGION | CHANGED_REGION_START))
        {
            Output("Resetting...");
            llResetScript();
        }
    }
}