integer SERVER_CUSTOM_HTTP_REQUEST = -1001;
integer SERVER_REGISTRATION_REQUEST = -1002;

integer SCRIPT_REGISTRATION_RESPONSE = -2002;
integer SCRIPT_CUSTOM_HTTP_RESPONSE = -10000000;

integer UNIQUE_ID = 153474138;


string BuildQueryResult()
{
    list agentsInRegion = llGetAgentList(AGENT_LIST_REGION, []);
    integer numAgentsInRegion = llGetListLength(agentsInRegion);

    string response = (string)numAgentsInRegion + ",";

    integer i;
    for(i = 0; i < numAgentsInRegion; i++)
    {
        key agentKey = llList2Key(agentsInRegion, i);
        list object_details = llGetObjectDetails(agentKey, [OBJECT_POS]);
        vector agentPos = llList2Vector(object_details, 0);

        string pos_x = (string)((integer)agentPos.x);
        string pos_y = (string)((integer)agentPos.y);
        string pos_z = (string)((integer)agentPos.z);

        response += (string)agentKey + "," + pos_x + "," + pos_y + "," + pos_z;

        if(i < numAgentsInRegion-1)
        {
            response += ",";
        }
    }

    return response;
}

LinkedHttpResponse(key id, integer status, string message)
{
    llMessageLinked(LINK_THIS, SCRIPT_CUSTOM_HTTP_RESPONSE - status, message, id);
}

integer ProcessRequest(list pathParts, key requestId)
{
    string firstPathPart = llList2String(pathParts, 0);

    if(firstPathPart == "Map")
    {
        string secondPathPart = llList2String(pathParts, 1);

        if(secondPathPart == "GetAgentList")
        {
            LinkedHttpResponse(requestId, 200, BuildQueryResult());
            return TRUE;
        }
        else if(secondPathPart == "GetRegionAgentCount")
        {
            LinkedHttpResponse(requestId, 200, (string)llGetRegionAgentCount());
            return TRUE;
        }
    }

    return FALSE;
}

default
{
    state_entry()
    {
        llOwnerSay("Module " + llGetScriptName() + " running");
    }

    link_message(integer sender_num, integer source, string body, key id)
    {
        if(source == SERVER_REGISTRATION_REQUEST)
        {
            llMessageLinked(LINK_THIS, SCRIPT_REGISTRATION_RESPONSE, "Map", (key)((string)UNIQUE_ID));
        }
        else if(source == UNIQUE_ID)
        {
            if(!ProcessRequest(llParseString2List(body, [","], []), id))
            {
                LinkedHttpResponse(id, 500, "Not implemented");
            }
        }
    }
}
