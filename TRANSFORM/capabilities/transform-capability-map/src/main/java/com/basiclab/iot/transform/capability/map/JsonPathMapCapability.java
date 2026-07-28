package com.basiclab.iot.transform.capability.map;
import com.basiclab.iot.transform.core.envelope.TransformEnvelope; import com.fasterxml.jackson.databind.*; import com.fasterxml.jackson.databind.node.*; import java.util.*;
/** Jackson JSON Pointer 字段映射实现。 */
public class JsonPathMapCapability implements MapCapability { private final ObjectMapper mapper; private final Map<String,Map<String,String>> rules;
 public JsonPathMapCapability(ObjectMapper mapper, Map<String,Map<String,String>> rules){this.mapper=mapper;this.rules=rules;}
 public TransformEnvelope map(String id, TransformEnvelope source){ Map<String,String> rule=rules.get(id); if(rule==null||rule.isEmpty()) return source; JsonNode input=mapper.valueToTree(source.getPayload()); ObjectNode target=mapper.createObjectNode(); rule.forEach((from,to)->set(target,to,input.at(pointer(from)))); source.setPayload(target); return source; }
 private String pointer(String p){return p.startsWith("/")?p:"/"+p.replace(".","/");} private void set(ObjectNode root,String path,JsonNode value){if(value==null||value.isMissingNode())return; String[] a=pointer(path).substring(1).split("/"); ObjectNode n=root; for(int i=0;i<a.length-1;i++) n=(ObjectNode)n.with(a[i]); n.set(a[a.length-1],value);}
}