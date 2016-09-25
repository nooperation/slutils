// Server data
string URL_REGISTER = "https://slutils-nooperation.c9users.io/server/register/";
string URL_UPDATE = "https://slutils-nooperation.c9users.io/server/update/";
string URL_CONFIRM = "https://slutils-nooperation.c9users.io/server/";


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

///////////////////////////////////////////////////////////////////////////////////////////////////////////
// ++++++  HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK
//                               FOR LOCAL OpenSim TESTING ONLY
///////////////////////////////////////////////////////////////////////////////////////////////////////////
/*
string JSON_OBJECT = "﷑";
string llList2Json( string type, list values )
{
    string buff = "{";
    integer numItems = llGetListLength(values);
    integer i;
    
    for(i = 0; i < numItems; i += 2)
    {
        string itemKey = llList2String(values, i);
        string itemValue = llList2String(values, i+1);
        
        buff += "\"" + itemKey + "\":\"" + itemValue + "\"";
                    
        if(i < numItems-2)
        {
            buff += ",";
        }
    }
    buff += "}";
    
    return buff;
}
*/
///////////////////////////////////////////////////////////////////////////////////////////////////////////
// ----- HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK
///////////////////////////////////////////////////////////////////////////////////////////////////////////

string BuildQueryResult()
{
    list agentsInRegion = llGetAgentList(AGENT_LIST_REGION, []);
    integer numAgentsInRegion = llGetListLength(agentsInRegion);
    
    string response = "{\"Players\":[";
    integer i;
    
    for(i = 0; i < numAgentsInRegion; i++)
    {
        key agentKey = llList2Key(agentsInRegion, i);
        vector agentPos = llGetPos(agentKey);
        
        string pos_x = (string)((integer)agentPos.x);
        string pos_y = (string)((integer)agentPos.y);
        string pos_z = (string)((integer)agentPos.z);
        
        response += llList2Json(JSON_OBJECT, [
            "Key", (string)agentKey,
            "Pos", "<" + pos_x + "," + pos_y + "," + pos_z + ">"
        ]);
        if(i < numAgentsInRegion-1)
        {
            response += ",";   
        }
    }
    
    response += "]}";
    
    return response;
}

integer ProcessRequest(list pathParts, key requestId)
{
    string firstPathPart = llList2String(pathParts, 0);
    //llOwnerSay("Request: " + llDumpList2String(pathParts, "|"));
    
    if(firstPathPart == "Base")
    {
        string secondPathPart = llList2String(pathParts, 1);
        
        if(secondPathPart == "GetAgentList")
        {
            llHTTPResponse(requestId, 200, BuildQueryResult());
            return TRUE;
        }
        else if(secondPathPart == "GetRegionAgentCount")
        {
            llHTTPResponse(requestId, 200, (string)llGetRegionAgentCount());
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
    
    return FALSE;
}

/// <summary>
/// 
/// </summary>
/// <param name="message">Message to output</param>
Output(string message)
{
    //llInstantMessage(llGetOwner(), message);
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
        urlRequestId = llRequestURL();
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
                Output("Updating server...");  
                updateRequestId = llHTTPRequest(URL_UPDATE, [HTTP_METHOD, "POST", HTTP_MIMETYPE,"application/x-www-form-urlencoded"], "address=" +  llEscapeURL(assignedUrl) + "&private_token=" + authToken); 
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
                string error_result = llJsonGetValue(body, ["Error"]);
                if(error_result != JSON_INVALID)
                {
                    Output("Failed to register server: " + error_result);
                    return;
                }
                
                string success_result = llJsonGetValue(body, ["Success"]);
                if(success_result != JSON_INVALID)
                {
                    Output("Registered!");
                    authToken = success_result;
                    Output("Base server registered. Now to configure it...");
                    state InitializeServer;
                }
                
                Output("Failed to register server: " + body);
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
            if(status == 200 && llGetSubString(body, 0, 2) == "OK.")
            {
                Output("Updated!");
                state ServerRunning;
            }
            else
            {
                Output("Failed to update: " + body);
                Output("Make sure your auth token is correct");
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
        llSetColor(<0, 1, 0>, ALL_SIDES);
        Output("Server running...");
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