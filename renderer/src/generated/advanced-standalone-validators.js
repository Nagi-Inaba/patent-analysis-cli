/* eslint-disable */
/* Generated closed advanced SVG validators. */
"use strict";
export const validateRequestRaw = validate20;
const schema31 = {"$id":"urn:patent-analysis:renderer-request:1.0.0","title":"RendererRequest 1.0.0","type":"object","additionalProperties":false,"required":["protocol_version","chart_model_b64","chart_model_sha256","render_spec_b64","render_spec_sha256"],"properties":{"protocol_version":{"const":"1.0.0"},"chart_model_b64":{"type":"string","minLength":4,"maxLength":2796204,"pattern":"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/][AQgw]==|[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=)?$"},"chart_model_sha256":{"type":"string","pattern":"^[0-9a-f]{64}$"},"render_spec_b64":{"type":"string","minLength":4,"maxLength":21848,"pattern":"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/][AQgw]==|[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=)?$"},"render_spec_sha256":{"type":"string","pattern":"^[0-9a-f]{64}$"}}};
function func1(value) {
  let length = 0;
  for (let index = 0; index < value.length; index++) {
    length++;
    const unit = value.charCodeAt(index);
    if (unit >= 0xD800 && unit <= 0xDBFF && index + 1 < value.length &&
        (value.charCodeAt(index + 1) & 0xFC00) === 0xDC00) index++;
  }
  return length;
}
const pattern4 = new RegExp("^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/][AQgw]==|[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=)?$", "u");
const pattern5 = new RegExp("^[0-9a-f]{64}$", "u");

function validate20(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
/*# sourceURL="urn:patent-analysis:renderer-request:1.0.0" */;
let vErrors = null;
let errors = 0;
const evaluated0 = validate20.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((data.protocol_version === undefined) && (missing0 = "protocol_version")) || ((data.chart_model_b64 === undefined) && (missing0 = "chart_model_b64"))) || ((data.chart_model_sha256 === undefined) && (missing0 = "chart_model_sha256"))) || ((data.render_spec_b64 === undefined) && (missing0 = "render_spec_b64"))) || ((data.render_spec_sha256 === undefined) && (missing0 = "render_spec_sha256"))){
validate20.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!(((((key0 === "protocol_version") || (key0 === "chart_model_b64")) || (key0 === "chart_model_sha256")) || (key0 === "render_spec_b64")) || (key0 === "render_spec_sha256"))){
validate20.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.protocol_version !== undefined){
const _errs2 = errors;
if("1.0.0" !== data.protocol_version){
validate20.errors = [{instancePath:instancePath+"/protocol_version",schemaPath:"#/properties/protocol_version/const",keyword:"const",params:{allowedValue: "1.0.0"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.chart_model_b64 !== undefined){
let data1 = data.chart_model_b64;
const _errs3 = errors;
if(errors === _errs3){
if(typeof data1 === "string"){
if(func1(data1) > 2796204){
validate20.errors = [{instancePath:instancePath+"/chart_model_b64",schemaPath:"#/properties/chart_model_b64/maxLength",keyword:"maxLength",params:{limit: 2796204},message:"must NOT have more than 2796204 characters"}];
return false;
}
else {
if(func1(data1) < 4){
validate20.errors = [{instancePath:instancePath+"/chart_model_b64",schemaPath:"#/properties/chart_model_b64/minLength",keyword:"minLength",params:{limit: 4},message:"must NOT have fewer than 4 characters"}];
return false;
}
else {
if(!pattern4.test(data1)){
validate20.errors = [{instancePath:instancePath+"/chart_model_b64",schemaPath:"#/properties/chart_model_b64/pattern",keyword:"pattern",params:{pattern: "^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/][AQgw]==|[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=)?$"},message:"must match pattern \""+"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/][AQgw]==|[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=)?$"+"\""}];
return false;
}
}
}
}
else {
validate20.errors = [{instancePath:instancePath+"/chart_model_b64",schemaPath:"#/properties/chart_model_b64/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.chart_model_sha256 !== undefined){
let data2 = data.chart_model_sha256;
const _errs5 = errors;
if(errors === _errs5){
if(typeof data2 === "string"){
if(!pattern5.test(data2)){
validate20.errors = [{instancePath:instancePath+"/chart_model_sha256",schemaPath:"#/properties/chart_model_sha256/pattern",keyword:"pattern",params:{pattern: "^[0-9a-f]{64}$"},message:"must match pattern \""+"^[0-9a-f]{64}$"+"\""}];
return false;
}
}
else {
validate20.errors = [{instancePath:instancePath+"/chart_model_sha256",schemaPath:"#/properties/chart_model_sha256/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.render_spec_b64 !== undefined){
let data3 = data.render_spec_b64;
const _errs7 = errors;
if(errors === _errs7){
if(typeof data3 === "string"){
if(func1(data3) > 21848){
validate20.errors = [{instancePath:instancePath+"/render_spec_b64",schemaPath:"#/properties/render_spec_b64/maxLength",keyword:"maxLength",params:{limit: 21848},message:"must NOT have more than 21848 characters"}];
return false;
}
else {
if(func1(data3) < 4){
validate20.errors = [{instancePath:instancePath+"/render_spec_b64",schemaPath:"#/properties/render_spec_b64/minLength",keyword:"minLength",params:{limit: 4},message:"must NOT have fewer than 4 characters"}];
return false;
}
else {
if(!pattern4.test(data3)){
validate20.errors = [{instancePath:instancePath+"/render_spec_b64",schemaPath:"#/properties/render_spec_b64/pattern",keyword:"pattern",params:{pattern: "^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/][AQgw]==|[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=)?$"},message:"must match pattern \""+"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/][AQgw]==|[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=)?$"+"\""}];
return false;
}
}
}
}
else {
validate20.errors = [{instancePath:instancePath+"/render_spec_b64",schemaPath:"#/properties/render_spec_b64/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs7 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.render_spec_sha256 !== undefined){
let data4 = data.render_spec_sha256;
const _errs9 = errors;
if(errors === _errs9){
if(typeof data4 === "string"){
if(!pattern5.test(data4)){
validate20.errors = [{instancePath:instancePath+"/render_spec_sha256",schemaPath:"#/properties/render_spec_sha256/pattern",keyword:"pattern",params:{pattern: "^[0-9a-f]{64}$"},message:"must match pattern \""+"^[0-9a-f]{64}$"+"\""}];
return false;
}
}
else {
validate20.errors = [{instancePath:instancePath+"/render_spec_sha256",schemaPath:"#/properties/render_spec_sha256/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs9 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
else {
validate20.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate20.errors = vErrors;
return errors === 0;
}
validate20.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const validateRuntimeRaw = validate21;
const schema32 = {"$id":"urn:patent-analysis:advanced-runtime:1.0.0","type":"object","additionalProperties":false,"required":["node_version","echarts_version","renderer_build_digest","render_profile_id"],"properties":{"node_version":{"const":"22.19.0"},"echarts_version":{"const":"6.1.0"},"renderer_build_digest":{"type":"string","pattern":"^[0-9a-f]{64}$"},"render_profile_id":{"const":"advanced-svg-ja-jp-node22-echarts6.v1"}}};

function validate21(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
/*# sourceURL="urn:patent-analysis:advanced-runtime:1.0.0" */;
let vErrors = null;
let errors = 0;
const evaluated0 = validate21.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((((data.node_version === undefined) && (missing0 = "node_version")) || ((data.echarts_version === undefined) && (missing0 = "echarts_version"))) || ((data.renderer_build_digest === undefined) && (missing0 = "renderer_build_digest"))) || ((data.render_profile_id === undefined) && (missing0 = "render_profile_id"))){
validate21.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((((key0 === "node_version") || (key0 === "echarts_version")) || (key0 === "renderer_build_digest")) || (key0 === "render_profile_id"))){
validate21.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.node_version !== undefined){
const _errs2 = errors;
if("22.19.0" !== data.node_version){
validate21.errors = [{instancePath:instancePath+"/node_version",schemaPath:"#/properties/node_version/const",keyword:"const",params:{allowedValue: "22.19.0"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.echarts_version !== undefined){
const _errs3 = errors;
if("6.1.0" !== data.echarts_version){
validate21.errors = [{instancePath:instancePath+"/echarts_version",schemaPath:"#/properties/echarts_version/const",keyword:"const",params:{allowedValue: "6.1.0"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.renderer_build_digest !== undefined){
let data2 = data.renderer_build_digest;
const _errs4 = errors;
if(errors === _errs4){
if(typeof data2 === "string"){
if(!pattern5.test(data2)){
validate21.errors = [{instancePath:instancePath+"/renderer_build_digest",schemaPath:"#/properties/renderer_build_digest/pattern",keyword:"pattern",params:{pattern: "^[0-9a-f]{64}$"},message:"must match pattern \""+"^[0-9a-f]{64}$"+"\""}];
return false;
}
}
else {
validate21.errors = [{instancePath:instancePath+"/renderer_build_digest",schemaPath:"#/properties/renderer_build_digest/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.render_profile_id !== undefined){
const _errs6 = errors;
if("advanced-svg-ja-jp-node22-echarts6.v1" !== data.render_profile_id){
validate21.errors = [{instancePath:instancePath+"/render_profile_id",schemaPath:"#/properties/render_profile_id/const",keyword:"const",params:{allowedValue: "advanced-svg-ja-jp-node22-echarts6.v1"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs6 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
else {
validate21.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate21.errors = vErrors;
return errors === 0;
}
validate21.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const validateModelRaw = validate22;
const schema33 = {"$id":"urn:patent-analysis:advanced-chart-model:1.0.0","type":"object","additionalProperties":false,"required":["chart_model_contract_version","chart_type","analysis_id","mark","title","analysis_result_sha256","projection","population","warnings"],"properties":{"chart_model_contract_version":{"const":"1.0.0"},"chart_type":{"const":"advanced.svg"},"analysis_id":{"type":"string"},"mark":{"type":"string"},"title":{"type":"string"},"analysis_result_sha256":{"type":"string","pattern":"^[0-9a-f]{64}$"},"projection":{"type":"object"},"population":{"type":"object","additionalProperties":false,"required":["input_rows","analyzed_rows","excluded_rows"],"properties":{"input_rows":{"type":"integer","minimum":0,"maximum":10000000},"analyzed_rows":{"type":"integer","minimum":0,"maximum":10000000},"excluded_rows":{"type":"integer","minimum":0,"maximum":10000000}}},"warnings":{"type":"array","maxItems":100,"items":{"type":"string","maxLength":4096}}},"anyOf":[{"properties":{"analysis_id":{"const":"growth-quadrant.v1"},"mark":{"const":"growth-quadrant-svg.v1"},"title":{"const":"長期・短期成長四象限"},"projection":{"$ref":"#/$defs/v1"}}},{"properties":{"analysis_id":{"const":"entry-exit.v1"},"mark":{"const":"entry-exit-svg.v1"},"title":{"const":"初回・最終観測年"},"projection":{"$ref":"#/$defs/v0","properties":{"x_year":{"const":true},"y_year":{"const":true},"x_label":{"const":"初回観測年"},"y_label":{"const":"最終観測年"},"size_label":{"const":"件数"},"points":{"type":"array","items":{"type":"object","properties":{"category":{"enum":["active","inactive"]}}}}},"type":"object"}}},{"properties":{"analysis_id":{"const":"citation.v1"},"mark":{"const":"citation-svg.v1"},"title":{"const":"レコード別被引用マップ"},"projection":{"$ref":"#/$defs/v0","properties":{"x_year":{"const":true},"y_year":{"const":false},"x_label":{"const":"観測年"},"y_label":{"const":"被引用件数"},"size_label":{"const":"被引用件数"},"points":{"type":"array","items":{"type":"object","properties":{"category":{"enum":["citation"]}}}}},"type":"object"}}},{"properties":{"analysis_id":{"const":"matrix-composition.v1"},"mark":{"const":"matrix-composition-svg.v1"},"title":{"const":"選択セルの構成内訳"},"projection":{"$ref":"#/$defs/v3"}}},{"properties":{"analysis_id":{"const":"new-entrants.v1"},"mark":{"const":"new-entrants-svg.v1"},"title":{"const":"母集団内の新規参入者と分類"},"projection":{"$ref":"#/$defs/v2"}}},{"properties":{"analysis_id":{"const":"compara.v1"},"mark":{"const":"compara-svg.v1"},"title":{"const":"グループ間の件数差分"},"projection":{"$ref":"#/$defs/v2"}}},{"properties":{"analysis_id":{"const":"cooccurrence.v1"},"mark":{"const":"cooccurrence-svg.v1"},"title":{"const":"分類の共起件数"},"projection":{"$ref":"#/$defs/v2"}}},{"properties":{"analysis_id":{"const":"collaboration-network.v1"},"mark":{"const":"collaboration-network-svg.v1"},"title":{"const":"共同関係ネットワーク"},"projection":{"$ref":"#/$defs/v4"}}},{"properties":{"analysis_id":{"const":"uniqueness.v1"},"mark":{"const":"uniqueness-svg.v1"},"title":{"const":"グループ別の固有項目"},"projection":{"$ref":"#/$defs/v3"}}},{"properties":{"analysis_id":{"const":"shared-involvement.v1"},"mark":{"const":"shared-involvement-svg.v1"},"title":{"const":"グループ別の共有項目と関与"},"projection":{"$ref":"#/$defs/v3"}}},{"properties":{"analysis_id":{"const":"inventor-tracking.v1"},"mark":{"const":"inventor-tracking-svg.v1"},"title":{"const":"発明者・共発明クラスタの年次追跡"},"projection":{"$ref":"#/$defs/v5"}}},{"properties":{"analysis_id":{"const":"inventor-network.v1"},"mark":{"const":"inventor-network-svg.v1"},"title":{"const":"共発明ネットワーク"},"projection":{"$ref":"#/$defs/v6"}}},{"properties":{"analysis_id":{"const":"inventor-ego-network.v1"},"mark":{"const":"inventor-ego-network-svg.v1"},"title":{"const":"発明者中心の関係マップ"},"projection":{"$ref":"#/$defs/v6","properties":{"focus":{"type":"string"}},"type":"object"}}},{"properties":{"analysis_id":{"const":"inventor-technology.v1"},"mark":{"const":"inventor-technology-svg.v1"},"title":{"const":"発明者×技術分野"},"projection":{"$ref":"#/$defs/v7"}}},{"properties":{"analysis_id":{"const":"inventor-activity.v1"},"mark":{"const":"inventor-activity-svg.v1"},"title":{"const":"発明者の活動履歴"},"projection":{"$ref":"#/$defs/v8","properties":{"bands":{"type":"array","maxItems":0}},"type":"object"}}},{"properties":{"analysis_id":{"const":"inventor-cluster-flow.v1"},"mark":{"const":"inventor-cluster-flow-svg.v1"},"title":{"const":"協働グループの変遷"},"projection":{"$ref":"#/$defs/v9"}}},{"properties":{"analysis_id":{"const":"inventor-similarity.v1"},"mark":{"const":"inventor-similarity-svg.v1"},"title":{"const":"発明者の技術類似度"},"projection":{"$ref":"#/$defs/v10"}}},{"properties":{"analysis_id":{"const":"inventor-impact.v1"},"mark":{"const":"inventor-impact-svg.v1"},"title":{"const":"発明者の活動量と引用指標"},"projection":{"$ref":"#/$defs/v10"}}},{"properties":{"analysis_id":{"const":"inventor-mobility.v1"},"mark":{"const":"inventor-mobility-svg.v1"},"title":{"const":"発明者と企業の関係変化"},"projection":{"$ref":"#/$defs/v8"}}},{"properties":{"analysis_id":{"const":"inventor-mobility-flow.v1"},"mark":{"const":"inventor-mobility-flow-svg.v1"},"title":{"const":"企業間の観測・移動フロー"},"projection":{"$ref":"#/$defs/v6","properties":{"edges":{"type":"array","items":{"type":"object","properties":{"directed":{"const":true}}}}},"type":"object"}}}],"$defs":{"t":{"type":"string","minLength":1,"maxLength":4096},"c":{"type":"string","maxLength":16384},"q":{"type":"number","minimum":-1000000000000,"maximum":1000000000000},"u":{"type":"number","minimum":0,"maximum":1000000000000},"g":{"type":"integer","minimum":0,"maximum":199},"y":{"type":"integer","minimum":1800,"maximum":2199},"r":{"type":"number","minimum":1800,"maximum":2200},"k":{"type":"integer","minimum":0,"maximum":499},"h":{"type":"integer","minimum":0,"maximum":19},"s":{"enum":["observed","inferred","confirmed"]},"p":{"type":"object","additionalProperties":false,"required":["id","label","x","y","size","category"],"properties":{"id":{"type":"string","pattern":"^[0-9]{1,3}$"},"label":{"type":"string","minLength":1,"maxLength":4096},"x":{"type":"number","minimum":-100,"maximum":1000000000000},"y":{"type":"number","minimum":-100,"maximum":1000000000000},"size":{"type":"number","minimum":0,"maximum":1000000000000},"category":{"enum":["sustained_growth","recovery","slowing","decline","empty","active","inactive","citation"]}}},"v0":{"type":"object","additionalProperties":false,"required":["kind","x_label","y_label","size_label","points","context","x_year","y_year"],"properties":{"kind":{"const":"scatter"},"x_label":{"$ref":"#/$defs/c"},"y_label":{"$ref":"#/$defs/c"},"size_label":{"$ref":"#/$defs/c"},"points":{"type":"array","maxItems":20,"items":{"$ref":"#/$defs/p"}},"context":{"$ref":"#/$defs/c"},"x_year":{"type":"boolean"},"y_year":{"type":"boolean"}}},"v1":{"type":"object","additionalProperties":false,"required":["kind","x_label","y_label","size_label","points","context","unplottable"],"properties":{"kind":{"const":"quadrant"},"x_label":{"$ref":"#/$defs/c"},"y_label":{"$ref":"#/$defs/c"},"size_label":{"$ref":"#/$defs/c"},"points":{"type":"array","maxItems":20,"items":{"$ref":"#/$defs/p"}},"context":{"$ref":"#/$defs/c"},"unplottable":{"type":"array","maxItems":20,"items":{"type":"object","additionalProperties":false,"required":["label","long_state","short_state","count"],"properties":{"label":{"$ref":"#/$defs/t"},"long_state":{"enum":["measured","new","empty"]},"short_state":{"enum":["measured","new","empty"]},"count":{"type":"integer","minimum":0,"maximum":1000000}}}}}},"v2":{"type":"object","additionalProperties":false,"required":["kind","x","y","x_label","y_label","signed","cells","context"],"properties":{"kind":{"const":"heatmap"},"x":{"type":"array","maxItems":20,"items":{"$ref":"#/$defs/t"}},"y":{"type":"array","maxItems":20,"items":{"$ref":"#/$defs/t"}},"x_label":{"$ref":"#/$defs/c"},"y_label":{"$ref":"#/$defs/c"},"signed":{"type":"boolean"},"cells":{"type":"array","maxItems":400,"items":{"type":"object","additionalProperties":false,"required":["x","y","value","share"],"properties":{"x":{"type":"integer","minimum":0,"maximum":19},"y":{"type":"integer","minimum":0,"maximum":19},"value":{"type":"number","minimum":-1000000,"maximum":1000000},"share":{"anyOf":[{"type":"number","minimum":0,"maximum":1},{"type":"null"}]}}}},"context":{"$ref":"#/$defs/c"}}},"v3":{"type":"object","additionalProperties":false,"required":["kind","value_label","items","context"],"properties":{"kind":{"const":"bars"},"value_label":{"$ref":"#/$defs/c"},"items":{"type":"array","maxItems":20,"items":{"type":"object","additionalProperties":false,"required":["label","value","denominator","share","record_count","involvement_count"],"properties":{"label":{"$ref":"#/$defs/t"},"value":{"type":"integer","minimum":0,"maximum":1000000},"denominator":{"type":"integer","minimum":0,"maximum":1000000},"share":{"type":"number","minimum":0,"maximum":1},"record_count":{"type":"integer","minimum":0,"maximum":1000000},"involvement_count":{"anyOf":[{"type":"integer","minimum":0,"maximum":1000000},{"type":"null"}]}}}},"context":{"$ref":"#/$defs/c"}}},"v4":{"type":"object","additionalProperties":false,"required":["kind","nodes","edges","context"],"properties":{"kind":{"const":"network"},"nodes":{"type":"array","maxItems":50,"items":{"type":"object","additionalProperties":false,"required":["label","value"],"properties":{"label":{"$ref":"#/$defs/t"},"value":{"type":"integer","minimum":1,"maximum":1000000}}}},"edges":{"type":"array","maxItems":80,"items":{"type":"object","additionalProperties":false,"required":["source","target","value"],"properties":{"source":{"type":"integer","minimum":0,"maximum":49},"target":{"type":"integer","minimum":0,"maximum":49},"value":{"type":"integer","minimum":1,"maximum":1000000}}}},"context":{"$ref":"#/$defs/c"}}},"v5":{"type":"object","additionalProperties":false,"required":["kind","years","inventors","nodes","links","context"],"properties":{"kind":{"const":"tracking"},"years":{"type":"array","items":{"type":"integer","minimum":1800,"maximum":2199},"maxItems":12},"inventors":{"type":"array","items":{"$ref":"#/$defs/t"},"maxItems":20},"nodes":{"type":"array","items":{"type":"object","additionalProperties":false,"required":["x","y","cluster","count","applicants","changed","unknown"],"properties":{"x":{"type":"integer","minimum":0,"maximum":11},"y":{"type":"integer","minimum":0,"maximum":19},"cluster":{"type":"integer","minimum":0,"maximum":19},"count":{"type":"integer","minimum":1,"maximum":100000},"applicants":{"$ref":"#/$defs/c"},"changed":{"type":"boolean"},"unknown":{"type":"boolean"}}},"maxItems":240},"links":{"type":"array","items":{"type":"object","additionalProperties":false,"required":["source","target","gap"],"properties":{"source":{"type":"integer","minimum":0,"maximum":239},"target":{"type":"integer","minimum":0,"maximum":239},"gap":{"type":"boolean"}}},"maxItems":220},"context":{"$ref":"#/$defs/c"}}},"v6":{"type":"object","additionalProperties":false,"minProperties":5,"properties":{"kind":{"const":"inventor-network"},"nodes":{"type":"array","maxItems":40,"items":{"type":"object","additionalProperties":false,"minProperties":7,"properties":{"id":{"$ref":"#/$defs/t"},"label":{"$ref":"#/$defs/t"},"x":{"$ref":"#/$defs/q"},"y":{"$ref":"#/$defs/q"},"value":{"$ref":"#/$defs/u"},"group":{"$ref":"#/$defs/g"},"hop":{"anyOf":[{"type":"integer","minimum":0,"maximum":3},{"type":"null"}]}}}},"edges":{"type":"array","maxItems":300,"items":{"type":"object","additionalProperties":false,"minProperties":5,"properties":{"source":{"$ref":"#/$defs/k"},"target":{"$ref":"#/$defs/k"},"value":{"$ref":"#/$defs/u"},"directed":{"type":"boolean"},"state":{"enum":["observed","inferred","confirmed","corporate"]}}}},"focus":{"anyOf":[{"$ref":"#/$defs/t"},{"type":"null"}]},"context":{"$ref":"#/$defs/c"}}},"v7":{"type":"object","additionalProperties":false,"minProperties":8,"properties":{"kind":{"const":"inventor-heatmap"},"x":{"type":"array","maxItems":20,"items":{"$ref":"#/$defs/t"}},"y":{"type":"array","maxItems":20,"items":{"$ref":"#/$defs/t"}},"x_label":{"$ref":"#/$defs/c"},"y_label":{"$ref":"#/$defs/c"},"value_label":{"$ref":"#/$defs/c"},"cells":{"type":"array","maxItems":400,"items":{"type":"object","additionalProperties":false,"minProperties":3,"properties":{"x":{"$ref":"#/$defs/h"},"y":{"$ref":"#/$defs/h"},"value":{"anyOf":[{"$ref":"#/$defs/u"},{"type":"null"}]}}}},"context":{"$ref":"#/$defs/c"}}},"v8":{"type":"object","additionalProperties":false,"minProperties":7,"properties":{"kind":{"const":"inventor-timeline"},"lanes":{"type":"array","maxItems":20,"items":{"$ref":"#/$defs/t"}},"years":{"type":"array","maxItems":30,"items":{"$ref":"#/$defs/y"}},"nodes":{"type":"array","maxItems":500,"items":{"type":"object","additionalProperties":false,"minProperties":7,"properties":{"id":{"$ref":"#/$defs/t"},"x":{"$ref":"#/$defs/r"},"y":{"$ref":"#/$defs/h"},"size":{"$ref":"#/$defs/u"},"category":{"$ref":"#/$defs/g"},"label":{"$ref":"#/$defs/t"},"state":{"enum":["observed","inferred","confirmed","unknown"]}}}},"links":{"type":"array","maxItems":500,"items":{"type":"object","additionalProperties":false,"minProperties":4,"properties":{"source":{"$ref":"#/$defs/k"},"target":{"$ref":"#/$defs/k"},"gap":{"type":"boolean"},"state":{"$ref":"#/$defs/s"}}}},"bands":{"type":"array","maxItems":100,"items":{"type":"object","additionalProperties":false,"minProperties":6,"properties":{"id":{"$ref":"#/$defs/t"},"start":{"$ref":"#/$defs/r"},"end":{"$ref":"#/$defs/r"},"label":{"$ref":"#/$defs/t"},"kind":{"enum":["acquisition","merger","name_change","group_change","rights_transfer","organizational_transfer"]},"status":{"enum":["announced","completed"]}}}},"context":{"$ref":"#/$defs/c"}}},"v9":{"type":"object","additionalProperties":false,"minProperties":5,"properties":{"kind":{"const":"inventor-alluvial"},"years":{"type":"array","maxItems":30,"items":{"$ref":"#/$defs/y"}},"nodes":{"type":"array","maxItems":100,"items":{"type":"object","additionalProperties":false,"minProperties":5,"properties":{"id":{"$ref":"#/$defs/t"},"label":{"$ref":"#/$defs/t"},"year":{"$ref":"#/$defs/y"},"members":{"type":"integer","minimum":0,"maximum":1000000},"kind":{"enum":["cluster","newly_observed","not_observed"]}}}},"links":{"type":"array","maxItems":300,"items":{"type":"object","additionalProperties":false,"minProperties":4,"properties":{"source":{"$ref":"#/$defs/k"},"target":{"$ref":"#/$defs/k"},"value":{"type":"integer","minimum":1,"maximum":1000000},"kind":{"enum":["continuation","split","merge","gap","newly_observed","not_observed"]}}}},"context":{"$ref":"#/$defs/c"}}},"v10":{"type":"object","additionalProperties":false,"minProperties":8,"properties":{"kind":{"const":"inventor-scatter"},"x_label":{"$ref":"#/$defs/c"},"y_label":{"$ref":"#/$defs/c"},"size_label":{"$ref":"#/$defs/c"},"points":{"type":"array","maxItems":40,"items":{"type":"object","additionalProperties":false,"minProperties":6,"properties":{"id":{"$ref":"#/$defs/t"},"label":{"$ref":"#/$defs/t"},"x":{"$ref":"#/$defs/q"},"y":{"$ref":"#/$defs/q"},"size":{"$ref":"#/$defs/u"},"category":{"type":"string","minLength":1,"maxLength":64}}}},"edges":{"type":"array","maxItems":300,"items":{"type":"object","additionalProperties":false,"minProperties":3,"properties":{"source":{"$ref":"#/$defs/k"},"target":{"$ref":"#/$defs/k"},"value":{"$ref":"#/$defs/u"}}}},"unplottable":{"type":"array","maxItems":200,"items":{"type":"object","additionalProperties":false,"minProperties":3,"properties":{"id":{"$ref":"#/$defs/t"},"label":{"$ref":"#/$defs/t"},"reason":{"$ref":"#/$defs/t"}}}},"context":{"$ref":"#/$defs/c"}}}}};
const schema34 = {"type":"object","additionalProperties":false,"required":["kind","x_label","y_label","size_label","points","context","unplottable"],"properties":{"kind":{"const":"quadrant"},"x_label":{"$ref":"#/$defs/c"},"y_label":{"$ref":"#/$defs/c"},"size_label":{"$ref":"#/$defs/c"},"points":{"type":"array","maxItems":20,"items":{"$ref":"#/$defs/p"}},"context":{"$ref":"#/$defs/c"},"unplottable":{"type":"array","maxItems":20,"items":{"type":"object","additionalProperties":false,"required":["label","long_state","short_state","count"],"properties":{"label":{"$ref":"#/$defs/t"},"long_state":{"enum":["measured","new","empty"]},"short_state":{"enum":["measured","new","empty"]},"count":{"type":"integer","minimum":0,"maximum":1000000}}}}}};
const schema35 = {"type":"string","maxLength":16384};
const schema38 = {"type":"object","additionalProperties":false,"required":["id","label","x","y","size","category"],"properties":{"id":{"type":"string","pattern":"^[0-9]{1,3}$"},"label":{"type":"string","minLength":1,"maxLength":4096},"x":{"type":"number","minimum":-100,"maximum":1000000000000},"y":{"type":"number","minimum":-100,"maximum":1000000000000},"size":{"type":"number","minimum":0,"maximum":1000000000000},"category":{"enum":["sustained_growth","recovery","slowing","decline","empty","active","inactive","citation"]}}};
const schema40 = {"type":"string","minLength":1,"maxLength":4096};
const pattern9 = new RegExp("^[0-9]{1,3}$", "u");

function validate23(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate23.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((((data.kind === undefined) && (missing0 = "kind")) || ((data.x_label === undefined) && (missing0 = "x_label"))) || ((data.y_label === undefined) && (missing0 = "y_label"))) || ((data.size_label === undefined) && (missing0 = "size_label"))) || ((data.points === undefined) && (missing0 = "points"))) || ((data.context === undefined) && (missing0 = "context"))) || ((data.unplottable === undefined) && (missing0 = "unplottable"))){
validate23.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!(((((((key0 === "kind") || (key0 === "x_label")) || (key0 === "y_label")) || (key0 === "size_label")) || (key0 === "points")) || (key0 === "context")) || (key0 === "unplottable"))){
validate23.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.kind !== undefined){
const _errs2 = errors;
if("quadrant" !== data.kind){
validate23.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/properties/kind/const",keyword:"const",params:{allowedValue: "quadrant"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.x_label !== undefined){
let data1 = data.x_label;
const _errs3 = errors;
const _errs4 = errors;
if(errors === _errs4){
if(typeof data1 === "string"){
if(func1(data1) > 16384){
validate23.errors = [{instancePath:instancePath+"/x_label",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate23.errors = [{instancePath:instancePath+"/x_label",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.y_label !== undefined){
let data2 = data.y_label;
const _errs6 = errors;
const _errs7 = errors;
if(errors === _errs7){
if(typeof data2 === "string"){
if(func1(data2) > 16384){
validate23.errors = [{instancePath:instancePath+"/y_label",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate23.errors = [{instancePath:instancePath+"/y_label",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs6 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.size_label !== undefined){
let data3 = data.size_label;
const _errs9 = errors;
const _errs10 = errors;
if(errors === _errs10){
if(typeof data3 === "string"){
if(func1(data3) > 16384){
validate23.errors = [{instancePath:instancePath+"/size_label",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate23.errors = [{instancePath:instancePath+"/size_label",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs9 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.points !== undefined){
let data4 = data.points;
const _errs12 = errors;
if(errors === _errs12){
if(Array.isArray(data4)){
if(data4.length > 20){
validate23.errors = [{instancePath:instancePath+"/points",schemaPath:"#/properties/points/maxItems",keyword:"maxItems",params:{limit: 20},message:"must NOT have more than 20 items"}];
return false;
}
else {
var valid4 = true;
const len0 = data4.length;
for(let i0=0; i0<len0; i0++){
let data5 = data4[i0];
const _errs14 = errors;
const _errs15 = errors;
if(errors === _errs15){
if(data5 && typeof data5 == "object" && !Array.isArray(data5)){
let missing1;
if(((((((data5.id === undefined) && (missing1 = "id")) || ((data5.label === undefined) && (missing1 = "label"))) || ((data5.x === undefined) && (missing1 = "x"))) || ((data5.y === undefined) && (missing1 = "y"))) || ((data5.size === undefined) && (missing1 = "size"))) || ((data5.category === undefined) && (missing1 = "category"))){
validate23.errors = [{instancePath:instancePath+"/points/" + i0,schemaPath:"#/$defs/p/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
const _errs17 = errors;
for(const key1 in data5){
if(!((((((key1 === "id") || (key1 === "label")) || (key1 === "x")) || (key1 === "y")) || (key1 === "size")) || (key1 === "category"))){
validate23.errors = [{instancePath:instancePath+"/points/" + i0,schemaPath:"#/$defs/p/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs17 === errors){
if(data5.id !== undefined){
let data6 = data5.id;
const _errs18 = errors;
if(errors === _errs18){
if(typeof data6 === "string"){
if(!pattern9.test(data6)){
validate23.errors = [{instancePath:instancePath+"/points/" + i0+"/id",schemaPath:"#/$defs/p/properties/id/pattern",keyword:"pattern",params:{pattern: "^[0-9]{1,3}$"},message:"must match pattern \""+"^[0-9]{1,3}$"+"\""}];
return false;
}
}
else {
validate23.errors = [{instancePath:instancePath+"/points/" + i0+"/id",schemaPath:"#/$defs/p/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid6 = _errs18 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data5.label !== undefined){
let data7 = data5.label;
const _errs20 = errors;
if(errors === _errs20){
if(typeof data7 === "string"){
if(func1(data7) > 4096){
validate23.errors = [{instancePath:instancePath+"/points/" + i0+"/label",schemaPath:"#/$defs/p/properties/label/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data7) < 1){
validate23.errors = [{instancePath:instancePath+"/points/" + i0+"/label",schemaPath:"#/$defs/p/properties/label/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/points/" + i0+"/label",schemaPath:"#/$defs/p/properties/label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid6 = _errs20 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data5.x !== undefined){
let data8 = data5.x;
const _errs22 = errors;
if(errors === _errs22){
if((typeof data8 == "number") && (isFinite(data8))){
if(data8 > 1000000000000 || isNaN(data8)){
validate23.errors = [{instancePath:instancePath+"/points/" + i0+"/x",schemaPath:"#/$defs/p/properties/x/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000000000},message:"must be <= 1000000000000"}];
return false;
}
else {
if(data8 < -100 || isNaN(data8)){
validate23.errors = [{instancePath:instancePath+"/points/" + i0+"/x",schemaPath:"#/$defs/p/properties/x/minimum",keyword:"minimum",params:{comparison: ">=", limit: -100},message:"must be >= -100"}];
return false;
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/points/" + i0+"/x",schemaPath:"#/$defs/p/properties/x/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid6 = _errs22 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data5.y !== undefined){
let data9 = data5.y;
const _errs24 = errors;
if(errors === _errs24){
if((typeof data9 == "number") && (isFinite(data9))){
if(data9 > 1000000000000 || isNaN(data9)){
validate23.errors = [{instancePath:instancePath+"/points/" + i0+"/y",schemaPath:"#/$defs/p/properties/y/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000000000},message:"must be <= 1000000000000"}];
return false;
}
else {
if(data9 < -100 || isNaN(data9)){
validate23.errors = [{instancePath:instancePath+"/points/" + i0+"/y",schemaPath:"#/$defs/p/properties/y/minimum",keyword:"minimum",params:{comparison: ">=", limit: -100},message:"must be >= -100"}];
return false;
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/points/" + i0+"/y",schemaPath:"#/$defs/p/properties/y/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid6 = _errs24 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data5.size !== undefined){
let data10 = data5.size;
const _errs26 = errors;
if(errors === _errs26){
if((typeof data10 == "number") && (isFinite(data10))){
if(data10 > 1000000000000 || isNaN(data10)){
validate23.errors = [{instancePath:instancePath+"/points/" + i0+"/size",schemaPath:"#/$defs/p/properties/size/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000000000},message:"must be <= 1000000000000"}];
return false;
}
else {
if(data10 < 0 || isNaN(data10)){
validate23.errors = [{instancePath:instancePath+"/points/" + i0+"/size",schemaPath:"#/$defs/p/properties/size/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/points/" + i0+"/size",schemaPath:"#/$defs/p/properties/size/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid6 = _errs26 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data5.category !== undefined){
let data11 = data5.category;
const _errs28 = errors;
if(!((((((((data11 === "sustained_growth") || (data11 === "recovery")) || (data11 === "slowing")) || (data11 === "decline")) || (data11 === "empty")) || (data11 === "active")) || (data11 === "inactive")) || (data11 === "citation"))){
validate23.errors = [{instancePath:instancePath+"/points/" + i0+"/category",schemaPath:"#/$defs/p/properties/category/enum",keyword:"enum",params:{allowedValues: schema38.properties.category.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid6 = _errs28 === errors;
}
else {
var valid6 = true;
}
}
}
}
}
}
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/points/" + i0,schemaPath:"#/$defs/p/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid4 = _errs14 === errors;
if(!valid4){
break;
}
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/points",schemaPath:"#/properties/points/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs12 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.context !== undefined){
let data12 = data.context;
const _errs29 = errors;
const _errs30 = errors;
if(errors === _errs30){
if(typeof data12 === "string"){
if(func1(data12) > 16384){
validate23.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate23.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs29 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.unplottable !== undefined){
let data13 = data.unplottable;
const _errs32 = errors;
if(errors === _errs32){
if(Array.isArray(data13)){
if(data13.length > 20){
validate23.errors = [{instancePath:instancePath+"/unplottable",schemaPath:"#/properties/unplottable/maxItems",keyword:"maxItems",params:{limit: 20},message:"must NOT have more than 20 items"}];
return false;
}
else {
var valid8 = true;
const len1 = data13.length;
for(let i1=0; i1<len1; i1++){
let data14 = data13[i1];
const _errs34 = errors;
if(errors === _errs34){
if(data14 && typeof data14 == "object" && !Array.isArray(data14)){
let missing2;
if(((((data14.label === undefined) && (missing2 = "label")) || ((data14.long_state === undefined) && (missing2 = "long_state"))) || ((data14.short_state === undefined) && (missing2 = "short_state"))) || ((data14.count === undefined) && (missing2 = "count"))){
validate23.errors = [{instancePath:instancePath+"/unplottable/" + i1,schemaPath:"#/properties/unplottable/items/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
const _errs36 = errors;
for(const key2 in data14){
if(!((((key2 === "label") || (key2 === "long_state")) || (key2 === "short_state")) || (key2 === "count"))){
validate23.errors = [{instancePath:instancePath+"/unplottable/" + i1,schemaPath:"#/properties/unplottable/items/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key2},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs36 === errors){
if(data14.label !== undefined){
let data15 = data14.label;
const _errs37 = errors;
const _errs38 = errors;
if(errors === _errs38){
if(typeof data15 === "string"){
if(func1(data15) > 4096){
validate23.errors = [{instancePath:instancePath+"/unplottable/" + i1+"/label",schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data15) < 1){
validate23.errors = [{instancePath:instancePath+"/unplottable/" + i1+"/label",schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/unplottable/" + i1+"/label",schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid9 = _errs37 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data14.long_state !== undefined){
let data16 = data14.long_state;
const _errs40 = errors;
if(!(((data16 === "measured") || (data16 === "new")) || (data16 === "empty"))){
validate23.errors = [{instancePath:instancePath+"/unplottable/" + i1+"/long_state",schemaPath:"#/properties/unplottable/items/properties/long_state/enum",keyword:"enum",params:{allowedValues: schema34.properties.unplottable.items.properties.long_state.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid9 = _errs40 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data14.short_state !== undefined){
let data17 = data14.short_state;
const _errs41 = errors;
if(!(((data17 === "measured") || (data17 === "new")) || (data17 === "empty"))){
validate23.errors = [{instancePath:instancePath+"/unplottable/" + i1+"/short_state",schemaPath:"#/properties/unplottable/items/properties/short_state/enum",keyword:"enum",params:{allowedValues: schema34.properties.unplottable.items.properties.short_state.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid9 = _errs41 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data14.count !== undefined){
let data18 = data14.count;
const _errs42 = errors;
if(!(((typeof data18 == "number") && (!(data18 % 1) && !isNaN(data18))) && (isFinite(data18)))){
validate23.errors = [{instancePath:instancePath+"/unplottable/" + i1+"/count",schemaPath:"#/properties/unplottable/items/properties/count/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs42){
if((typeof data18 == "number") && (isFinite(data18))){
if(data18 > 1000000 || isNaN(data18)){
validate23.errors = [{instancePath:instancePath+"/unplottable/" + i1+"/count",schemaPath:"#/properties/unplottable/items/properties/count/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000},message:"must be <= 1000000"}];
return false;
}
else {
if(data18 < 0 || isNaN(data18)){
validate23.errors = [{instancePath:instancePath+"/unplottable/" + i1+"/count",schemaPath:"#/properties/unplottable/items/properties/count/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid9 = _errs42 === errors;
}
else {
var valid9 = true;
}
}
}
}
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/unplottable/" + i1,schemaPath:"#/properties/unplottable/items/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid8 = _errs34 === errors;
if(!valid8){
break;
}
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/unplottable",schemaPath:"#/properties/unplottable/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs32 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
else {
validate23.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate23.errors = vErrors;
return errors === 0;
}
validate23.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const schema41 = {"type":"object","additionalProperties":false,"required":["kind","x_label","y_label","size_label","points","context","x_year","y_year"],"properties":{"kind":{"const":"scatter"},"x_label":{"$ref":"#/$defs/c"},"y_label":{"$ref":"#/$defs/c"},"size_label":{"$ref":"#/$defs/c"},"points":{"type":"array","maxItems":20,"items":{"$ref":"#/$defs/p"}},"context":{"$ref":"#/$defs/c"},"x_year":{"type":"boolean"},"y_year":{"type":"boolean"}}};

function validate25(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate25.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((((((((data.kind === undefined) && (missing0 = "kind")) || ((data.x_label === undefined) && (missing0 = "x_label"))) || ((data.y_label === undefined) && (missing0 = "y_label"))) || ((data.size_label === undefined) && (missing0 = "size_label"))) || ((data.points === undefined) && (missing0 = "points"))) || ((data.context === undefined) && (missing0 = "context"))) || ((data.x_year === undefined) && (missing0 = "x_year"))) || ((data.y_year === undefined) && (missing0 = "y_year"))){
validate25.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((((((((key0 === "kind") || (key0 === "x_label")) || (key0 === "y_label")) || (key0 === "size_label")) || (key0 === "points")) || (key0 === "context")) || (key0 === "x_year")) || (key0 === "y_year"))){
validate25.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.kind !== undefined){
const _errs2 = errors;
if("scatter" !== data.kind){
validate25.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/properties/kind/const",keyword:"const",params:{allowedValue: "scatter"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.x_label !== undefined){
let data1 = data.x_label;
const _errs3 = errors;
const _errs4 = errors;
if(errors === _errs4){
if(typeof data1 === "string"){
if(func1(data1) > 16384){
validate25.errors = [{instancePath:instancePath+"/x_label",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate25.errors = [{instancePath:instancePath+"/x_label",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.y_label !== undefined){
let data2 = data.y_label;
const _errs6 = errors;
const _errs7 = errors;
if(errors === _errs7){
if(typeof data2 === "string"){
if(func1(data2) > 16384){
validate25.errors = [{instancePath:instancePath+"/y_label",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate25.errors = [{instancePath:instancePath+"/y_label",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs6 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.size_label !== undefined){
let data3 = data.size_label;
const _errs9 = errors;
const _errs10 = errors;
if(errors === _errs10){
if(typeof data3 === "string"){
if(func1(data3) > 16384){
validate25.errors = [{instancePath:instancePath+"/size_label",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate25.errors = [{instancePath:instancePath+"/size_label",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs9 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.points !== undefined){
let data4 = data.points;
const _errs12 = errors;
if(errors === _errs12){
if(Array.isArray(data4)){
if(data4.length > 20){
validate25.errors = [{instancePath:instancePath+"/points",schemaPath:"#/properties/points/maxItems",keyword:"maxItems",params:{limit: 20},message:"must NOT have more than 20 items"}];
return false;
}
else {
var valid4 = true;
const len0 = data4.length;
for(let i0=0; i0<len0; i0++){
let data5 = data4[i0];
const _errs14 = errors;
const _errs15 = errors;
if(errors === _errs15){
if(data5 && typeof data5 == "object" && !Array.isArray(data5)){
let missing1;
if(((((((data5.id === undefined) && (missing1 = "id")) || ((data5.label === undefined) && (missing1 = "label"))) || ((data5.x === undefined) && (missing1 = "x"))) || ((data5.y === undefined) && (missing1 = "y"))) || ((data5.size === undefined) && (missing1 = "size"))) || ((data5.category === undefined) && (missing1 = "category"))){
validate25.errors = [{instancePath:instancePath+"/points/" + i0,schemaPath:"#/$defs/p/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
const _errs17 = errors;
for(const key1 in data5){
if(!((((((key1 === "id") || (key1 === "label")) || (key1 === "x")) || (key1 === "y")) || (key1 === "size")) || (key1 === "category"))){
validate25.errors = [{instancePath:instancePath+"/points/" + i0,schemaPath:"#/$defs/p/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs17 === errors){
if(data5.id !== undefined){
let data6 = data5.id;
const _errs18 = errors;
if(errors === _errs18){
if(typeof data6 === "string"){
if(!pattern9.test(data6)){
validate25.errors = [{instancePath:instancePath+"/points/" + i0+"/id",schemaPath:"#/$defs/p/properties/id/pattern",keyword:"pattern",params:{pattern: "^[0-9]{1,3}$"},message:"must match pattern \""+"^[0-9]{1,3}$"+"\""}];
return false;
}
}
else {
validate25.errors = [{instancePath:instancePath+"/points/" + i0+"/id",schemaPath:"#/$defs/p/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid6 = _errs18 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data5.label !== undefined){
let data7 = data5.label;
const _errs20 = errors;
if(errors === _errs20){
if(typeof data7 === "string"){
if(func1(data7) > 4096){
validate25.errors = [{instancePath:instancePath+"/points/" + i0+"/label",schemaPath:"#/$defs/p/properties/label/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data7) < 1){
validate25.errors = [{instancePath:instancePath+"/points/" + i0+"/label",schemaPath:"#/$defs/p/properties/label/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate25.errors = [{instancePath:instancePath+"/points/" + i0+"/label",schemaPath:"#/$defs/p/properties/label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid6 = _errs20 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data5.x !== undefined){
let data8 = data5.x;
const _errs22 = errors;
if(errors === _errs22){
if((typeof data8 == "number") && (isFinite(data8))){
if(data8 > 1000000000000 || isNaN(data8)){
validate25.errors = [{instancePath:instancePath+"/points/" + i0+"/x",schemaPath:"#/$defs/p/properties/x/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000000000},message:"must be <= 1000000000000"}];
return false;
}
else {
if(data8 < -100 || isNaN(data8)){
validate25.errors = [{instancePath:instancePath+"/points/" + i0+"/x",schemaPath:"#/$defs/p/properties/x/minimum",keyword:"minimum",params:{comparison: ">=", limit: -100},message:"must be >= -100"}];
return false;
}
}
}
else {
validate25.errors = [{instancePath:instancePath+"/points/" + i0+"/x",schemaPath:"#/$defs/p/properties/x/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid6 = _errs22 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data5.y !== undefined){
let data9 = data5.y;
const _errs24 = errors;
if(errors === _errs24){
if((typeof data9 == "number") && (isFinite(data9))){
if(data9 > 1000000000000 || isNaN(data9)){
validate25.errors = [{instancePath:instancePath+"/points/" + i0+"/y",schemaPath:"#/$defs/p/properties/y/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000000000},message:"must be <= 1000000000000"}];
return false;
}
else {
if(data9 < -100 || isNaN(data9)){
validate25.errors = [{instancePath:instancePath+"/points/" + i0+"/y",schemaPath:"#/$defs/p/properties/y/minimum",keyword:"minimum",params:{comparison: ">=", limit: -100},message:"must be >= -100"}];
return false;
}
}
}
else {
validate25.errors = [{instancePath:instancePath+"/points/" + i0+"/y",schemaPath:"#/$defs/p/properties/y/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid6 = _errs24 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data5.size !== undefined){
let data10 = data5.size;
const _errs26 = errors;
if(errors === _errs26){
if((typeof data10 == "number") && (isFinite(data10))){
if(data10 > 1000000000000 || isNaN(data10)){
validate25.errors = [{instancePath:instancePath+"/points/" + i0+"/size",schemaPath:"#/$defs/p/properties/size/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000000000},message:"must be <= 1000000000000"}];
return false;
}
else {
if(data10 < 0 || isNaN(data10)){
validate25.errors = [{instancePath:instancePath+"/points/" + i0+"/size",schemaPath:"#/$defs/p/properties/size/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
else {
validate25.errors = [{instancePath:instancePath+"/points/" + i0+"/size",schemaPath:"#/$defs/p/properties/size/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid6 = _errs26 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data5.category !== undefined){
let data11 = data5.category;
const _errs28 = errors;
if(!((((((((data11 === "sustained_growth") || (data11 === "recovery")) || (data11 === "slowing")) || (data11 === "decline")) || (data11 === "empty")) || (data11 === "active")) || (data11 === "inactive")) || (data11 === "citation"))){
validate25.errors = [{instancePath:instancePath+"/points/" + i0+"/category",schemaPath:"#/$defs/p/properties/category/enum",keyword:"enum",params:{allowedValues: schema38.properties.category.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid6 = _errs28 === errors;
}
else {
var valid6 = true;
}
}
}
}
}
}
}
}
}
else {
validate25.errors = [{instancePath:instancePath+"/points/" + i0,schemaPath:"#/$defs/p/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid4 = _errs14 === errors;
if(!valid4){
break;
}
}
}
}
else {
validate25.errors = [{instancePath:instancePath+"/points",schemaPath:"#/properties/points/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs12 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.context !== undefined){
let data12 = data.context;
const _errs29 = errors;
const _errs30 = errors;
if(errors === _errs30){
if(typeof data12 === "string"){
if(func1(data12) > 16384){
validate25.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate25.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs29 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.x_year !== undefined){
const _errs32 = errors;
if(typeof data.x_year !== "boolean"){
validate25.errors = [{instancePath:instancePath+"/x_year",schemaPath:"#/properties/x_year/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs32 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.y_year !== undefined){
const _errs34 = errors;
if(typeof data.y_year !== "boolean"){
validate25.errors = [{instancePath:instancePath+"/y_year",schemaPath:"#/properties/y_year/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs34 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
validate25.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate25.errors = vErrors;
return errors === 0;
}
validate25.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const schema47 = {"type":"object","additionalProperties":false,"required":["kind","value_label","items","context"],"properties":{"kind":{"const":"bars"},"value_label":{"$ref":"#/$defs/c"},"items":{"type":"array","maxItems":20,"items":{"type":"object","additionalProperties":false,"required":["label","value","denominator","share","record_count","involvement_count"],"properties":{"label":{"$ref":"#/$defs/t"},"value":{"type":"integer","minimum":0,"maximum":1000000},"denominator":{"type":"integer","minimum":0,"maximum":1000000},"share":{"type":"number","minimum":0,"maximum":1},"record_count":{"type":"integer","minimum":0,"maximum":1000000},"involvement_count":{"anyOf":[{"type":"integer","minimum":0,"maximum":1000000},{"type":"null"}]}}}},"context":{"$ref":"#/$defs/c"}}};

function validate28(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate28.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((((data.kind === undefined) && (missing0 = "kind")) || ((data.value_label === undefined) && (missing0 = "value_label"))) || ((data.items === undefined) && (missing0 = "items"))) || ((data.context === undefined) && (missing0 = "context"))){
validate28.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((((key0 === "kind") || (key0 === "value_label")) || (key0 === "items")) || (key0 === "context"))){
validate28.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.kind !== undefined){
const _errs2 = errors;
if("bars" !== data.kind){
validate28.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/properties/kind/const",keyword:"const",params:{allowedValue: "bars"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.value_label !== undefined){
let data1 = data.value_label;
const _errs3 = errors;
const _errs4 = errors;
if(errors === _errs4){
if(typeof data1 === "string"){
if(func1(data1) > 16384){
validate28.errors = [{instancePath:instancePath+"/value_label",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate28.errors = [{instancePath:instancePath+"/value_label",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.items !== undefined){
let data2 = data.items;
const _errs6 = errors;
if(errors === _errs6){
if(Array.isArray(data2)){
if(data2.length > 20){
validate28.errors = [{instancePath:instancePath+"/items",schemaPath:"#/properties/items/maxItems",keyword:"maxItems",params:{limit: 20},message:"must NOT have more than 20 items"}];
return false;
}
else {
var valid2 = true;
const len0 = data2.length;
for(let i0=0; i0<len0; i0++){
let data3 = data2[i0];
const _errs8 = errors;
if(errors === _errs8){
if(data3 && typeof data3 == "object" && !Array.isArray(data3)){
let missing1;
if(((((((data3.label === undefined) && (missing1 = "label")) || ((data3.value === undefined) && (missing1 = "value"))) || ((data3.denominator === undefined) && (missing1 = "denominator"))) || ((data3.share === undefined) && (missing1 = "share"))) || ((data3.record_count === undefined) && (missing1 = "record_count"))) || ((data3.involvement_count === undefined) && (missing1 = "involvement_count"))){
validate28.errors = [{instancePath:instancePath+"/items/" + i0,schemaPath:"#/properties/items/items/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
const _errs10 = errors;
for(const key1 in data3){
if(!((((((key1 === "label") || (key1 === "value")) || (key1 === "denominator")) || (key1 === "share")) || (key1 === "record_count")) || (key1 === "involvement_count"))){
validate28.errors = [{instancePath:instancePath+"/items/" + i0,schemaPath:"#/properties/items/items/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs10 === errors){
if(data3.label !== undefined){
let data4 = data3.label;
const _errs11 = errors;
const _errs12 = errors;
if(errors === _errs12){
if(typeof data4 === "string"){
if(func1(data4) > 4096){
validate28.errors = [{instancePath:instancePath+"/items/" + i0+"/label",schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data4) < 1){
validate28.errors = [{instancePath:instancePath+"/items/" + i0+"/label",schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate28.errors = [{instancePath:instancePath+"/items/" + i0+"/label",schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid3 = _errs11 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.value !== undefined){
let data5 = data3.value;
const _errs14 = errors;
if(!(((typeof data5 == "number") && (!(data5 % 1) && !isNaN(data5))) && (isFinite(data5)))){
validate28.errors = [{instancePath:instancePath+"/items/" + i0+"/value",schemaPath:"#/properties/items/items/properties/value/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs14){
if((typeof data5 == "number") && (isFinite(data5))){
if(data5 > 1000000 || isNaN(data5)){
validate28.errors = [{instancePath:instancePath+"/items/" + i0+"/value",schemaPath:"#/properties/items/items/properties/value/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000},message:"must be <= 1000000"}];
return false;
}
else {
if(data5 < 0 || isNaN(data5)){
validate28.errors = [{instancePath:instancePath+"/items/" + i0+"/value",schemaPath:"#/properties/items/items/properties/value/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid3 = _errs14 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.denominator !== undefined){
let data6 = data3.denominator;
const _errs16 = errors;
if(!(((typeof data6 == "number") && (!(data6 % 1) && !isNaN(data6))) && (isFinite(data6)))){
validate28.errors = [{instancePath:instancePath+"/items/" + i0+"/denominator",schemaPath:"#/properties/items/items/properties/denominator/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs16){
if((typeof data6 == "number") && (isFinite(data6))){
if(data6 > 1000000 || isNaN(data6)){
validate28.errors = [{instancePath:instancePath+"/items/" + i0+"/denominator",schemaPath:"#/properties/items/items/properties/denominator/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000},message:"must be <= 1000000"}];
return false;
}
else {
if(data6 < 0 || isNaN(data6)){
validate28.errors = [{instancePath:instancePath+"/items/" + i0+"/denominator",schemaPath:"#/properties/items/items/properties/denominator/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid3 = _errs16 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.share !== undefined){
let data7 = data3.share;
const _errs18 = errors;
if(errors === _errs18){
if((typeof data7 == "number") && (isFinite(data7))){
if(data7 > 1 || isNaN(data7)){
validate28.errors = [{instancePath:instancePath+"/items/" + i0+"/share",schemaPath:"#/properties/items/items/properties/share/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1},message:"must be <= 1"}];
return false;
}
else {
if(data7 < 0 || isNaN(data7)){
validate28.errors = [{instancePath:instancePath+"/items/" + i0+"/share",schemaPath:"#/properties/items/items/properties/share/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
else {
validate28.errors = [{instancePath:instancePath+"/items/" + i0+"/share",schemaPath:"#/properties/items/items/properties/share/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid3 = _errs18 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.record_count !== undefined){
let data8 = data3.record_count;
const _errs20 = errors;
if(!(((typeof data8 == "number") && (!(data8 % 1) && !isNaN(data8))) && (isFinite(data8)))){
validate28.errors = [{instancePath:instancePath+"/items/" + i0+"/record_count",schemaPath:"#/properties/items/items/properties/record_count/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs20){
if((typeof data8 == "number") && (isFinite(data8))){
if(data8 > 1000000 || isNaN(data8)){
validate28.errors = [{instancePath:instancePath+"/items/" + i0+"/record_count",schemaPath:"#/properties/items/items/properties/record_count/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000},message:"must be <= 1000000"}];
return false;
}
else {
if(data8 < 0 || isNaN(data8)){
validate28.errors = [{instancePath:instancePath+"/items/" + i0+"/record_count",schemaPath:"#/properties/items/items/properties/record_count/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid3 = _errs20 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data3.involvement_count !== undefined){
let data9 = data3.involvement_count;
const _errs22 = errors;
const _errs23 = errors;
let valid5 = false;
const _errs24 = errors;
if(!(((typeof data9 == "number") && (!(data9 % 1) && !isNaN(data9))) && (isFinite(data9)))){
const err0 = {instancePath:instancePath+"/items/" + i0+"/involvement_count",schemaPath:"#/properties/items/items/properties/involvement_count/anyOf/0/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
if(errors === _errs24){
if((typeof data9 == "number") && (isFinite(data9))){
if(data9 > 1000000 || isNaN(data9)){
const err1 = {instancePath:instancePath+"/items/" + i0+"/involvement_count",schemaPath:"#/properties/items/items/properties/involvement_count/anyOf/0/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000},message:"must be <= 1000000"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
else {
if(data9 < 0 || isNaN(data9)){
const err2 = {instancePath:instancePath+"/items/" + i0+"/involvement_count",schemaPath:"#/properties/items/items/properties/involvement_count/anyOf/0/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
}
}
}
var _valid0 = _errs24 === errors;
valid5 = valid5 || _valid0;
const _errs26 = errors;
if(data9 !== null){
const err3 = {instancePath:instancePath+"/items/" + i0+"/involvement_count",schemaPath:"#/properties/items/items/properties/involvement_count/anyOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
var _valid0 = _errs26 === errors;
valid5 = valid5 || _valid0;
if(!valid5){
const err4 = {instancePath:instancePath+"/items/" + i0+"/involvement_count",schemaPath:"#/properties/items/items/properties/involvement_count/anyOf",keyword:"anyOf",params:{},message:"must match a schema in anyOf"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
validate28.errors = vErrors;
return false;
}
else {
errors = _errs23;
if(vErrors !== null){
if(_errs23){
vErrors.length = _errs23;
}
else {
vErrors = null;
}
}
}
var valid3 = _errs22 === errors;
}
else {
var valid3 = true;
}
}
}
}
}
}
}
}
}
else {
validate28.errors = [{instancePath:instancePath+"/items/" + i0,schemaPath:"#/properties/items/items/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid2 = _errs8 === errors;
if(!valid2){
break;
}
}
}
}
else {
validate28.errors = [{instancePath:instancePath+"/items",schemaPath:"#/properties/items/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs6 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.context !== undefined){
let data10 = data.context;
const _errs28 = errors;
const _errs29 = errors;
if(errors === _errs29){
if(typeof data10 === "string"){
if(func1(data10) > 16384){
validate28.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate28.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs28 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
else {
validate28.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate28.errors = vErrors;
return errors === 0;
}
validate28.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const schema51 = {"type":"object","additionalProperties":false,"required":["kind","x","y","x_label","y_label","signed","cells","context"],"properties":{"kind":{"const":"heatmap"},"x":{"type":"array","maxItems":20,"items":{"$ref":"#/$defs/t"}},"y":{"type":"array","maxItems":20,"items":{"$ref":"#/$defs/t"}},"x_label":{"$ref":"#/$defs/c"},"y_label":{"$ref":"#/$defs/c"},"signed":{"type":"boolean"},"cells":{"type":"array","maxItems":400,"items":{"type":"object","additionalProperties":false,"required":["x","y","value","share"],"properties":{"x":{"type":"integer","minimum":0,"maximum":19},"y":{"type":"integer","minimum":0,"maximum":19},"value":{"type":"number","minimum":-1000000,"maximum":1000000},"share":{"anyOf":[{"type":"number","minimum":0,"maximum":1},{"type":"null"}]}}}},"context":{"$ref":"#/$defs/c"}}};

function validate30(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate30.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((((((((data.kind === undefined) && (missing0 = "kind")) || ((data.x === undefined) && (missing0 = "x"))) || ((data.y === undefined) && (missing0 = "y"))) || ((data.x_label === undefined) && (missing0 = "x_label"))) || ((data.y_label === undefined) && (missing0 = "y_label"))) || ((data.signed === undefined) && (missing0 = "signed"))) || ((data.cells === undefined) && (missing0 = "cells"))) || ((data.context === undefined) && (missing0 = "context"))){
validate30.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((((((((key0 === "kind") || (key0 === "x")) || (key0 === "y")) || (key0 === "x_label")) || (key0 === "y_label")) || (key0 === "signed")) || (key0 === "cells")) || (key0 === "context"))){
validate30.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.kind !== undefined){
const _errs2 = errors;
if("heatmap" !== data.kind){
validate30.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/properties/kind/const",keyword:"const",params:{allowedValue: "heatmap"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.x !== undefined){
let data1 = data.x;
const _errs3 = errors;
if(errors === _errs3){
if(Array.isArray(data1)){
if(data1.length > 20){
validate30.errors = [{instancePath:instancePath+"/x",schemaPath:"#/properties/x/maxItems",keyword:"maxItems",params:{limit: 20},message:"must NOT have more than 20 items"}];
return false;
}
else {
var valid1 = true;
const len0 = data1.length;
for(let i0=0; i0<len0; i0++){
let data2 = data1[i0];
const _errs5 = errors;
const _errs6 = errors;
if(errors === _errs6){
if(typeof data2 === "string"){
if(func1(data2) > 4096){
validate30.errors = [{instancePath:instancePath+"/x/" + i0,schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data2) < 1){
validate30.errors = [{instancePath:instancePath+"/x/" + i0,schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate30.errors = [{instancePath:instancePath+"/x/" + i0,schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid1 = _errs5 === errors;
if(!valid1){
break;
}
}
}
}
else {
validate30.errors = [{instancePath:instancePath+"/x",schemaPath:"#/properties/x/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.y !== undefined){
let data3 = data.y;
const _errs8 = errors;
if(errors === _errs8){
if(Array.isArray(data3)){
if(data3.length > 20){
validate30.errors = [{instancePath:instancePath+"/y",schemaPath:"#/properties/y/maxItems",keyword:"maxItems",params:{limit: 20},message:"must NOT have more than 20 items"}];
return false;
}
else {
var valid3 = true;
const len1 = data3.length;
for(let i1=0; i1<len1; i1++){
let data4 = data3[i1];
const _errs10 = errors;
const _errs11 = errors;
if(errors === _errs11){
if(typeof data4 === "string"){
if(func1(data4) > 4096){
validate30.errors = [{instancePath:instancePath+"/y/" + i1,schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data4) < 1){
validate30.errors = [{instancePath:instancePath+"/y/" + i1,schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate30.errors = [{instancePath:instancePath+"/y/" + i1,schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid3 = _errs10 === errors;
if(!valid3){
break;
}
}
}
}
else {
validate30.errors = [{instancePath:instancePath+"/y",schemaPath:"#/properties/y/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs8 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.x_label !== undefined){
let data5 = data.x_label;
const _errs13 = errors;
const _errs14 = errors;
if(errors === _errs14){
if(typeof data5 === "string"){
if(func1(data5) > 16384){
validate30.errors = [{instancePath:instancePath+"/x_label",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate30.errors = [{instancePath:instancePath+"/x_label",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs13 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.y_label !== undefined){
let data6 = data.y_label;
const _errs16 = errors;
const _errs17 = errors;
if(errors === _errs17){
if(typeof data6 === "string"){
if(func1(data6) > 16384){
validate30.errors = [{instancePath:instancePath+"/y_label",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate30.errors = [{instancePath:instancePath+"/y_label",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs16 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.signed !== undefined){
const _errs19 = errors;
if(typeof data.signed !== "boolean"){
validate30.errors = [{instancePath:instancePath+"/signed",schemaPath:"#/properties/signed/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid0 = _errs19 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.cells !== undefined){
let data8 = data.cells;
const _errs21 = errors;
if(errors === _errs21){
if(Array.isArray(data8)){
if(data8.length > 400){
validate30.errors = [{instancePath:instancePath+"/cells",schemaPath:"#/properties/cells/maxItems",keyword:"maxItems",params:{limit: 400},message:"must NOT have more than 400 items"}];
return false;
}
else {
var valid7 = true;
const len2 = data8.length;
for(let i2=0; i2<len2; i2++){
let data9 = data8[i2];
const _errs23 = errors;
if(errors === _errs23){
if(data9 && typeof data9 == "object" && !Array.isArray(data9)){
let missing1;
if(((((data9.x === undefined) && (missing1 = "x")) || ((data9.y === undefined) && (missing1 = "y"))) || ((data9.value === undefined) && (missing1 = "value"))) || ((data9.share === undefined) && (missing1 = "share"))){
validate30.errors = [{instancePath:instancePath+"/cells/" + i2,schemaPath:"#/properties/cells/items/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
const _errs25 = errors;
for(const key1 in data9){
if(!((((key1 === "x") || (key1 === "y")) || (key1 === "value")) || (key1 === "share"))){
validate30.errors = [{instancePath:instancePath+"/cells/" + i2,schemaPath:"#/properties/cells/items/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs25 === errors){
if(data9.x !== undefined){
let data10 = data9.x;
const _errs26 = errors;
if(!(((typeof data10 == "number") && (!(data10 % 1) && !isNaN(data10))) && (isFinite(data10)))){
validate30.errors = [{instancePath:instancePath+"/cells/" + i2+"/x",schemaPath:"#/properties/cells/items/properties/x/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs26){
if((typeof data10 == "number") && (isFinite(data10))){
if(data10 > 19 || isNaN(data10)){
validate30.errors = [{instancePath:instancePath+"/cells/" + i2+"/x",schemaPath:"#/properties/cells/items/properties/x/maximum",keyword:"maximum",params:{comparison: "<=", limit: 19},message:"must be <= 19"}];
return false;
}
else {
if(data10 < 0 || isNaN(data10)){
validate30.errors = [{instancePath:instancePath+"/cells/" + i2+"/x",schemaPath:"#/properties/cells/items/properties/x/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid8 = _errs26 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data9.y !== undefined){
let data11 = data9.y;
const _errs28 = errors;
if(!(((typeof data11 == "number") && (!(data11 % 1) && !isNaN(data11))) && (isFinite(data11)))){
validate30.errors = [{instancePath:instancePath+"/cells/" + i2+"/y",schemaPath:"#/properties/cells/items/properties/y/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs28){
if((typeof data11 == "number") && (isFinite(data11))){
if(data11 > 19 || isNaN(data11)){
validate30.errors = [{instancePath:instancePath+"/cells/" + i2+"/y",schemaPath:"#/properties/cells/items/properties/y/maximum",keyword:"maximum",params:{comparison: "<=", limit: 19},message:"must be <= 19"}];
return false;
}
else {
if(data11 < 0 || isNaN(data11)){
validate30.errors = [{instancePath:instancePath+"/cells/" + i2+"/y",schemaPath:"#/properties/cells/items/properties/y/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid8 = _errs28 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data9.value !== undefined){
let data12 = data9.value;
const _errs30 = errors;
if(errors === _errs30){
if((typeof data12 == "number") && (isFinite(data12))){
if(data12 > 1000000 || isNaN(data12)){
validate30.errors = [{instancePath:instancePath+"/cells/" + i2+"/value",schemaPath:"#/properties/cells/items/properties/value/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000},message:"must be <= 1000000"}];
return false;
}
else {
if(data12 < -1000000 || isNaN(data12)){
validate30.errors = [{instancePath:instancePath+"/cells/" + i2+"/value",schemaPath:"#/properties/cells/items/properties/value/minimum",keyword:"minimum",params:{comparison: ">=", limit: -1000000},message:"must be >= -1000000"}];
return false;
}
}
}
else {
validate30.errors = [{instancePath:instancePath+"/cells/" + i2+"/value",schemaPath:"#/properties/cells/items/properties/value/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid8 = _errs30 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data9.share !== undefined){
let data13 = data9.share;
const _errs32 = errors;
const _errs33 = errors;
let valid9 = false;
const _errs34 = errors;
if(errors === _errs34){
if((typeof data13 == "number") && (isFinite(data13))){
if(data13 > 1 || isNaN(data13)){
const err0 = {instancePath:instancePath+"/cells/" + i2+"/share",schemaPath:"#/properties/cells/items/properties/share/anyOf/0/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1},message:"must be <= 1"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
else {
if(data13 < 0 || isNaN(data13)){
const err1 = {instancePath:instancePath+"/cells/" + i2+"/share",schemaPath:"#/properties/cells/items/properties/share/anyOf/0/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
}
}
else {
const err2 = {instancePath:instancePath+"/cells/" + i2+"/share",schemaPath:"#/properties/cells/items/properties/share/anyOf/0/type",keyword:"type",params:{type: "number"},message:"must be number"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
}
var _valid0 = _errs34 === errors;
valid9 = valid9 || _valid0;
const _errs36 = errors;
if(data13 !== null){
const err3 = {instancePath:instancePath+"/cells/" + i2+"/share",schemaPath:"#/properties/cells/items/properties/share/anyOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
var _valid0 = _errs36 === errors;
valid9 = valid9 || _valid0;
if(!valid9){
const err4 = {instancePath:instancePath+"/cells/" + i2+"/share",schemaPath:"#/properties/cells/items/properties/share/anyOf",keyword:"anyOf",params:{},message:"must match a schema in anyOf"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
validate30.errors = vErrors;
return false;
}
else {
errors = _errs33;
if(vErrors !== null){
if(_errs33){
vErrors.length = _errs33;
}
else {
vErrors = null;
}
}
}
var valid8 = _errs32 === errors;
}
else {
var valid8 = true;
}
}
}
}
}
}
}
else {
validate30.errors = [{instancePath:instancePath+"/cells/" + i2,schemaPath:"#/properties/cells/items/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid7 = _errs23 === errors;
if(!valid7){
break;
}
}
}
}
else {
validate30.errors = [{instancePath:instancePath+"/cells",schemaPath:"#/properties/cells/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs21 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.context !== undefined){
let data14 = data.context;
const _errs38 = errors;
const _errs39 = errors;
if(errors === _errs39){
if(typeof data14 === "string"){
if(func1(data14) > 16384){
validate30.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate30.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs38 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
validate30.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate30.errors = vErrors;
return errors === 0;
}
validate30.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const schema57 = {"type":"object","additionalProperties":false,"required":["kind","nodes","edges","context"],"properties":{"kind":{"const":"network"},"nodes":{"type":"array","maxItems":50,"items":{"type":"object","additionalProperties":false,"required":["label","value"],"properties":{"label":{"$ref":"#/$defs/t"},"value":{"type":"integer","minimum":1,"maximum":1000000}}}},"edges":{"type":"array","maxItems":80,"items":{"type":"object","additionalProperties":false,"required":["source","target","value"],"properties":{"source":{"type":"integer","minimum":0,"maximum":49},"target":{"type":"integer","minimum":0,"maximum":49},"value":{"type":"integer","minimum":1,"maximum":1000000}}}},"context":{"$ref":"#/$defs/c"}}};

function validate34(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate34.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((((data.kind === undefined) && (missing0 = "kind")) || ((data.nodes === undefined) && (missing0 = "nodes"))) || ((data.edges === undefined) && (missing0 = "edges"))) || ((data.context === undefined) && (missing0 = "context"))){
validate34.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((((key0 === "kind") || (key0 === "nodes")) || (key0 === "edges")) || (key0 === "context"))){
validate34.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.kind !== undefined){
const _errs2 = errors;
if("network" !== data.kind){
validate34.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/properties/kind/const",keyword:"const",params:{allowedValue: "network"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.nodes !== undefined){
let data1 = data.nodes;
const _errs3 = errors;
if(errors === _errs3){
if(Array.isArray(data1)){
if(data1.length > 50){
validate34.errors = [{instancePath:instancePath+"/nodes",schemaPath:"#/properties/nodes/maxItems",keyword:"maxItems",params:{limit: 50},message:"must NOT have more than 50 items"}];
return false;
}
else {
var valid1 = true;
const len0 = data1.length;
for(let i0=0; i0<len0; i0++){
let data2 = data1[i0];
const _errs5 = errors;
if(errors === _errs5){
if(data2 && typeof data2 == "object" && !Array.isArray(data2)){
let missing1;
if(((data2.label === undefined) && (missing1 = "label")) || ((data2.value === undefined) && (missing1 = "value"))){
validate34.errors = [{instancePath:instancePath+"/nodes/" + i0,schemaPath:"#/properties/nodes/items/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
const _errs7 = errors;
for(const key1 in data2){
if(!((key1 === "label") || (key1 === "value"))){
validate34.errors = [{instancePath:instancePath+"/nodes/" + i0,schemaPath:"#/properties/nodes/items/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs7 === errors){
if(data2.label !== undefined){
let data3 = data2.label;
const _errs8 = errors;
const _errs9 = errors;
if(errors === _errs9){
if(typeof data3 === "string"){
if(func1(data3) > 4096){
validate34.errors = [{instancePath:instancePath+"/nodes/" + i0+"/label",schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data3) < 1){
validate34.errors = [{instancePath:instancePath+"/nodes/" + i0+"/label",schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate34.errors = [{instancePath:instancePath+"/nodes/" + i0+"/label",schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid2 = _errs8 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data2.value !== undefined){
let data4 = data2.value;
const _errs11 = errors;
if(!(((typeof data4 == "number") && (!(data4 % 1) && !isNaN(data4))) && (isFinite(data4)))){
validate34.errors = [{instancePath:instancePath+"/nodes/" + i0+"/value",schemaPath:"#/properties/nodes/items/properties/value/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs11){
if((typeof data4 == "number") && (isFinite(data4))){
if(data4 > 1000000 || isNaN(data4)){
validate34.errors = [{instancePath:instancePath+"/nodes/" + i0+"/value",schemaPath:"#/properties/nodes/items/properties/value/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000},message:"must be <= 1000000"}];
return false;
}
else {
if(data4 < 1 || isNaN(data4)){
validate34.errors = [{instancePath:instancePath+"/nodes/" + i0+"/value",schemaPath:"#/properties/nodes/items/properties/value/minimum",keyword:"minimum",params:{comparison: ">=", limit: 1},message:"must be >= 1"}];
return false;
}
}
}
}
var valid2 = _errs11 === errors;
}
else {
var valid2 = true;
}
}
}
}
}
else {
validate34.errors = [{instancePath:instancePath+"/nodes/" + i0,schemaPath:"#/properties/nodes/items/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid1 = _errs5 === errors;
if(!valid1){
break;
}
}
}
}
else {
validate34.errors = [{instancePath:instancePath+"/nodes",schemaPath:"#/properties/nodes/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.edges !== undefined){
let data5 = data.edges;
const _errs13 = errors;
if(errors === _errs13){
if(Array.isArray(data5)){
if(data5.length > 80){
validate34.errors = [{instancePath:instancePath+"/edges",schemaPath:"#/properties/edges/maxItems",keyword:"maxItems",params:{limit: 80},message:"must NOT have more than 80 items"}];
return false;
}
else {
var valid4 = true;
const len1 = data5.length;
for(let i1=0; i1<len1; i1++){
let data6 = data5[i1];
const _errs15 = errors;
if(errors === _errs15){
if(data6 && typeof data6 == "object" && !Array.isArray(data6)){
let missing2;
if((((data6.source === undefined) && (missing2 = "source")) || ((data6.target === undefined) && (missing2 = "target"))) || ((data6.value === undefined) && (missing2 = "value"))){
validate34.errors = [{instancePath:instancePath+"/edges/" + i1,schemaPath:"#/properties/edges/items/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
const _errs17 = errors;
for(const key2 in data6){
if(!(((key2 === "source") || (key2 === "target")) || (key2 === "value"))){
validate34.errors = [{instancePath:instancePath+"/edges/" + i1,schemaPath:"#/properties/edges/items/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key2},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs17 === errors){
if(data6.source !== undefined){
let data7 = data6.source;
const _errs18 = errors;
if(!(((typeof data7 == "number") && (!(data7 % 1) && !isNaN(data7))) && (isFinite(data7)))){
validate34.errors = [{instancePath:instancePath+"/edges/" + i1+"/source",schemaPath:"#/properties/edges/items/properties/source/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs18){
if((typeof data7 == "number") && (isFinite(data7))){
if(data7 > 49 || isNaN(data7)){
validate34.errors = [{instancePath:instancePath+"/edges/" + i1+"/source",schemaPath:"#/properties/edges/items/properties/source/maximum",keyword:"maximum",params:{comparison: "<=", limit: 49},message:"must be <= 49"}];
return false;
}
else {
if(data7 < 0 || isNaN(data7)){
validate34.errors = [{instancePath:instancePath+"/edges/" + i1+"/source",schemaPath:"#/properties/edges/items/properties/source/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid5 = _errs18 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data6.target !== undefined){
let data8 = data6.target;
const _errs20 = errors;
if(!(((typeof data8 == "number") && (!(data8 % 1) && !isNaN(data8))) && (isFinite(data8)))){
validate34.errors = [{instancePath:instancePath+"/edges/" + i1+"/target",schemaPath:"#/properties/edges/items/properties/target/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs20){
if((typeof data8 == "number") && (isFinite(data8))){
if(data8 > 49 || isNaN(data8)){
validate34.errors = [{instancePath:instancePath+"/edges/" + i1+"/target",schemaPath:"#/properties/edges/items/properties/target/maximum",keyword:"maximum",params:{comparison: "<=", limit: 49},message:"must be <= 49"}];
return false;
}
else {
if(data8 < 0 || isNaN(data8)){
validate34.errors = [{instancePath:instancePath+"/edges/" + i1+"/target",schemaPath:"#/properties/edges/items/properties/target/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid5 = _errs20 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data6.value !== undefined){
let data9 = data6.value;
const _errs22 = errors;
if(!(((typeof data9 == "number") && (!(data9 % 1) && !isNaN(data9))) && (isFinite(data9)))){
validate34.errors = [{instancePath:instancePath+"/edges/" + i1+"/value",schemaPath:"#/properties/edges/items/properties/value/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs22){
if((typeof data9 == "number") && (isFinite(data9))){
if(data9 > 1000000 || isNaN(data9)){
validate34.errors = [{instancePath:instancePath+"/edges/" + i1+"/value",schemaPath:"#/properties/edges/items/properties/value/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000},message:"must be <= 1000000"}];
return false;
}
else {
if(data9 < 1 || isNaN(data9)){
validate34.errors = [{instancePath:instancePath+"/edges/" + i1+"/value",schemaPath:"#/properties/edges/items/properties/value/minimum",keyword:"minimum",params:{comparison: ">=", limit: 1},message:"must be >= 1"}];
return false;
}
}
}
}
var valid5 = _errs22 === errors;
}
else {
var valid5 = true;
}
}
}
}
}
}
else {
validate34.errors = [{instancePath:instancePath+"/edges/" + i1,schemaPath:"#/properties/edges/items/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid4 = _errs15 === errors;
if(!valid4){
break;
}
}
}
}
else {
validate34.errors = [{instancePath:instancePath+"/edges",schemaPath:"#/properties/edges/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs13 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.context !== undefined){
let data10 = data.context;
const _errs24 = errors;
const _errs25 = errors;
if(errors === _errs25){
if(typeof data10 === "string"){
if(func1(data10) > 16384){
validate34.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate34.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs24 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
else {
validate34.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate34.errors = vErrors;
return errors === 0;
}
validate34.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const schema60 = {"type":"object","additionalProperties":false,"required":["kind","years","inventors","nodes","links","context"],"properties":{"kind":{"const":"tracking"},"years":{"type":"array","items":{"type":"integer","minimum":1800,"maximum":2199},"maxItems":12},"inventors":{"type":"array","items":{"$ref":"#/$defs/t"},"maxItems":20},"nodes":{"type":"array","items":{"type":"object","additionalProperties":false,"required":["x","y","cluster","count","applicants","changed","unknown"],"properties":{"x":{"type":"integer","minimum":0,"maximum":11},"y":{"type":"integer","minimum":0,"maximum":19},"cluster":{"type":"integer","minimum":0,"maximum":19},"count":{"type":"integer","minimum":1,"maximum":100000},"applicants":{"$ref":"#/$defs/c"},"changed":{"type":"boolean"},"unknown":{"type":"boolean"}}},"maxItems":240},"links":{"type":"array","items":{"type":"object","additionalProperties":false,"required":["source","target","gap"],"properties":{"source":{"type":"integer","minimum":0,"maximum":239},"target":{"type":"integer","minimum":0,"maximum":239},"gap":{"type":"boolean"}}},"maxItems":220},"context":{"$ref":"#/$defs/c"}}};

function validate38(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate38.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((((((data.kind === undefined) && (missing0 = "kind")) || ((data.years === undefined) && (missing0 = "years"))) || ((data.inventors === undefined) && (missing0 = "inventors"))) || ((data.nodes === undefined) && (missing0 = "nodes"))) || ((data.links === undefined) && (missing0 = "links"))) || ((data.context === undefined) && (missing0 = "context"))){
validate38.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((((((key0 === "kind") || (key0 === "years")) || (key0 === "inventors")) || (key0 === "nodes")) || (key0 === "links")) || (key0 === "context"))){
validate38.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.kind !== undefined){
const _errs2 = errors;
if("tracking" !== data.kind){
validate38.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/properties/kind/const",keyword:"const",params:{allowedValue: "tracking"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.years !== undefined){
let data1 = data.years;
const _errs3 = errors;
if(errors === _errs3){
if(Array.isArray(data1)){
if(data1.length > 12){
validate38.errors = [{instancePath:instancePath+"/years",schemaPath:"#/properties/years/maxItems",keyword:"maxItems",params:{limit: 12},message:"must NOT have more than 12 items"}];
return false;
}
else {
var valid1 = true;
const len0 = data1.length;
for(let i0=0; i0<len0; i0++){
let data2 = data1[i0];
const _errs5 = errors;
if(!(((typeof data2 == "number") && (!(data2 % 1) && !isNaN(data2))) && (isFinite(data2)))){
validate38.errors = [{instancePath:instancePath+"/years/" + i0,schemaPath:"#/properties/years/items/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs5){
if((typeof data2 == "number") && (isFinite(data2))){
if(data2 > 2199 || isNaN(data2)){
validate38.errors = [{instancePath:instancePath+"/years/" + i0,schemaPath:"#/properties/years/items/maximum",keyword:"maximum",params:{comparison: "<=", limit: 2199},message:"must be <= 2199"}];
return false;
}
else {
if(data2 < 1800 || isNaN(data2)){
validate38.errors = [{instancePath:instancePath+"/years/" + i0,schemaPath:"#/properties/years/items/minimum",keyword:"minimum",params:{comparison: ">=", limit: 1800},message:"must be >= 1800"}];
return false;
}
}
}
}
var valid1 = _errs5 === errors;
if(!valid1){
break;
}
}
}
}
else {
validate38.errors = [{instancePath:instancePath+"/years",schemaPath:"#/properties/years/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.inventors !== undefined){
let data3 = data.inventors;
const _errs7 = errors;
if(errors === _errs7){
if(Array.isArray(data3)){
if(data3.length > 20){
validate38.errors = [{instancePath:instancePath+"/inventors",schemaPath:"#/properties/inventors/maxItems",keyword:"maxItems",params:{limit: 20},message:"must NOT have more than 20 items"}];
return false;
}
else {
var valid2 = true;
const len1 = data3.length;
for(let i1=0; i1<len1; i1++){
let data4 = data3[i1];
const _errs9 = errors;
const _errs10 = errors;
if(errors === _errs10){
if(typeof data4 === "string"){
if(func1(data4) > 4096){
validate38.errors = [{instancePath:instancePath+"/inventors/" + i1,schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data4) < 1){
validate38.errors = [{instancePath:instancePath+"/inventors/" + i1,schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate38.errors = [{instancePath:instancePath+"/inventors/" + i1,schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid2 = _errs9 === errors;
if(!valid2){
break;
}
}
}
}
else {
validate38.errors = [{instancePath:instancePath+"/inventors",schemaPath:"#/properties/inventors/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs7 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.nodes !== undefined){
let data5 = data.nodes;
const _errs12 = errors;
if(errors === _errs12){
if(Array.isArray(data5)){
if(data5.length > 240){
validate38.errors = [{instancePath:instancePath+"/nodes",schemaPath:"#/properties/nodes/maxItems",keyword:"maxItems",params:{limit: 240},message:"must NOT have more than 240 items"}];
return false;
}
else {
var valid4 = true;
const len2 = data5.length;
for(let i2=0; i2<len2; i2++){
let data6 = data5[i2];
const _errs14 = errors;
if(errors === _errs14){
if(data6 && typeof data6 == "object" && !Array.isArray(data6)){
let missing1;
if((((((((data6.x === undefined) && (missing1 = "x")) || ((data6.y === undefined) && (missing1 = "y"))) || ((data6.cluster === undefined) && (missing1 = "cluster"))) || ((data6.count === undefined) && (missing1 = "count"))) || ((data6.applicants === undefined) && (missing1 = "applicants"))) || ((data6.changed === undefined) && (missing1 = "changed"))) || ((data6.unknown === undefined) && (missing1 = "unknown"))){
validate38.errors = [{instancePath:instancePath+"/nodes/" + i2,schemaPath:"#/properties/nodes/items/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
const _errs16 = errors;
for(const key1 in data6){
if(!(((((((key1 === "x") || (key1 === "y")) || (key1 === "cluster")) || (key1 === "count")) || (key1 === "applicants")) || (key1 === "changed")) || (key1 === "unknown"))){
validate38.errors = [{instancePath:instancePath+"/nodes/" + i2,schemaPath:"#/properties/nodes/items/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs16 === errors){
if(data6.x !== undefined){
let data7 = data6.x;
const _errs17 = errors;
if(!(((typeof data7 == "number") && (!(data7 % 1) && !isNaN(data7))) && (isFinite(data7)))){
validate38.errors = [{instancePath:instancePath+"/nodes/" + i2+"/x",schemaPath:"#/properties/nodes/items/properties/x/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs17){
if((typeof data7 == "number") && (isFinite(data7))){
if(data7 > 11 || isNaN(data7)){
validate38.errors = [{instancePath:instancePath+"/nodes/" + i2+"/x",schemaPath:"#/properties/nodes/items/properties/x/maximum",keyword:"maximum",params:{comparison: "<=", limit: 11},message:"must be <= 11"}];
return false;
}
else {
if(data7 < 0 || isNaN(data7)){
validate38.errors = [{instancePath:instancePath+"/nodes/" + i2+"/x",schemaPath:"#/properties/nodes/items/properties/x/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid5 = _errs17 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data6.y !== undefined){
let data8 = data6.y;
const _errs19 = errors;
if(!(((typeof data8 == "number") && (!(data8 % 1) && !isNaN(data8))) && (isFinite(data8)))){
validate38.errors = [{instancePath:instancePath+"/nodes/" + i2+"/y",schemaPath:"#/properties/nodes/items/properties/y/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs19){
if((typeof data8 == "number") && (isFinite(data8))){
if(data8 > 19 || isNaN(data8)){
validate38.errors = [{instancePath:instancePath+"/nodes/" + i2+"/y",schemaPath:"#/properties/nodes/items/properties/y/maximum",keyword:"maximum",params:{comparison: "<=", limit: 19},message:"must be <= 19"}];
return false;
}
else {
if(data8 < 0 || isNaN(data8)){
validate38.errors = [{instancePath:instancePath+"/nodes/" + i2+"/y",schemaPath:"#/properties/nodes/items/properties/y/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid5 = _errs19 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data6.cluster !== undefined){
let data9 = data6.cluster;
const _errs21 = errors;
if(!(((typeof data9 == "number") && (!(data9 % 1) && !isNaN(data9))) && (isFinite(data9)))){
validate38.errors = [{instancePath:instancePath+"/nodes/" + i2+"/cluster",schemaPath:"#/properties/nodes/items/properties/cluster/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs21){
if((typeof data9 == "number") && (isFinite(data9))){
if(data9 > 19 || isNaN(data9)){
validate38.errors = [{instancePath:instancePath+"/nodes/" + i2+"/cluster",schemaPath:"#/properties/nodes/items/properties/cluster/maximum",keyword:"maximum",params:{comparison: "<=", limit: 19},message:"must be <= 19"}];
return false;
}
else {
if(data9 < 0 || isNaN(data9)){
validate38.errors = [{instancePath:instancePath+"/nodes/" + i2+"/cluster",schemaPath:"#/properties/nodes/items/properties/cluster/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid5 = _errs21 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data6.count !== undefined){
let data10 = data6.count;
const _errs23 = errors;
if(!(((typeof data10 == "number") && (!(data10 % 1) && !isNaN(data10))) && (isFinite(data10)))){
validate38.errors = [{instancePath:instancePath+"/nodes/" + i2+"/count",schemaPath:"#/properties/nodes/items/properties/count/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs23){
if((typeof data10 == "number") && (isFinite(data10))){
if(data10 > 100000 || isNaN(data10)){
validate38.errors = [{instancePath:instancePath+"/nodes/" + i2+"/count",schemaPath:"#/properties/nodes/items/properties/count/maximum",keyword:"maximum",params:{comparison: "<=", limit: 100000},message:"must be <= 100000"}];
return false;
}
else {
if(data10 < 1 || isNaN(data10)){
validate38.errors = [{instancePath:instancePath+"/nodes/" + i2+"/count",schemaPath:"#/properties/nodes/items/properties/count/minimum",keyword:"minimum",params:{comparison: ">=", limit: 1},message:"must be >= 1"}];
return false;
}
}
}
}
var valid5 = _errs23 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data6.applicants !== undefined){
let data11 = data6.applicants;
const _errs25 = errors;
const _errs26 = errors;
if(errors === _errs26){
if(typeof data11 === "string"){
if(func1(data11) > 16384){
validate38.errors = [{instancePath:instancePath+"/nodes/" + i2+"/applicants",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate38.errors = [{instancePath:instancePath+"/nodes/" + i2+"/applicants",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid5 = _errs25 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data6.changed !== undefined){
const _errs28 = errors;
if(typeof data6.changed !== "boolean"){
validate38.errors = [{instancePath:instancePath+"/nodes/" + i2+"/changed",schemaPath:"#/properties/nodes/items/properties/changed/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid5 = _errs28 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data6.unknown !== undefined){
const _errs30 = errors;
if(typeof data6.unknown !== "boolean"){
validate38.errors = [{instancePath:instancePath+"/nodes/" + i2+"/unknown",schemaPath:"#/properties/nodes/items/properties/unknown/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid5 = _errs30 === errors;
}
else {
var valid5 = true;
}
}
}
}
}
}
}
}
}
}
else {
validate38.errors = [{instancePath:instancePath+"/nodes/" + i2,schemaPath:"#/properties/nodes/items/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid4 = _errs14 === errors;
if(!valid4){
break;
}
}
}
}
else {
validate38.errors = [{instancePath:instancePath+"/nodes",schemaPath:"#/properties/nodes/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs12 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.links !== undefined){
let data14 = data.links;
const _errs32 = errors;
if(errors === _errs32){
if(Array.isArray(data14)){
if(data14.length > 220){
validate38.errors = [{instancePath:instancePath+"/links",schemaPath:"#/properties/links/maxItems",keyword:"maxItems",params:{limit: 220},message:"must NOT have more than 220 items"}];
return false;
}
else {
var valid7 = true;
const len3 = data14.length;
for(let i3=0; i3<len3; i3++){
let data15 = data14[i3];
const _errs34 = errors;
if(errors === _errs34){
if(data15 && typeof data15 == "object" && !Array.isArray(data15)){
let missing2;
if((((data15.source === undefined) && (missing2 = "source")) || ((data15.target === undefined) && (missing2 = "target"))) || ((data15.gap === undefined) && (missing2 = "gap"))){
validate38.errors = [{instancePath:instancePath+"/links/" + i3,schemaPath:"#/properties/links/items/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
const _errs36 = errors;
for(const key2 in data15){
if(!(((key2 === "source") || (key2 === "target")) || (key2 === "gap"))){
validate38.errors = [{instancePath:instancePath+"/links/" + i3,schemaPath:"#/properties/links/items/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key2},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs36 === errors){
if(data15.source !== undefined){
let data16 = data15.source;
const _errs37 = errors;
if(!(((typeof data16 == "number") && (!(data16 % 1) && !isNaN(data16))) && (isFinite(data16)))){
validate38.errors = [{instancePath:instancePath+"/links/" + i3+"/source",schemaPath:"#/properties/links/items/properties/source/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs37){
if((typeof data16 == "number") && (isFinite(data16))){
if(data16 > 239 || isNaN(data16)){
validate38.errors = [{instancePath:instancePath+"/links/" + i3+"/source",schemaPath:"#/properties/links/items/properties/source/maximum",keyword:"maximum",params:{comparison: "<=", limit: 239},message:"must be <= 239"}];
return false;
}
else {
if(data16 < 0 || isNaN(data16)){
validate38.errors = [{instancePath:instancePath+"/links/" + i3+"/source",schemaPath:"#/properties/links/items/properties/source/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid8 = _errs37 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data15.target !== undefined){
let data17 = data15.target;
const _errs39 = errors;
if(!(((typeof data17 == "number") && (!(data17 % 1) && !isNaN(data17))) && (isFinite(data17)))){
validate38.errors = [{instancePath:instancePath+"/links/" + i3+"/target",schemaPath:"#/properties/links/items/properties/target/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs39){
if((typeof data17 == "number") && (isFinite(data17))){
if(data17 > 239 || isNaN(data17)){
validate38.errors = [{instancePath:instancePath+"/links/" + i3+"/target",schemaPath:"#/properties/links/items/properties/target/maximum",keyword:"maximum",params:{comparison: "<=", limit: 239},message:"must be <= 239"}];
return false;
}
else {
if(data17 < 0 || isNaN(data17)){
validate38.errors = [{instancePath:instancePath+"/links/" + i3+"/target",schemaPath:"#/properties/links/items/properties/target/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid8 = _errs39 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data15.gap !== undefined){
const _errs41 = errors;
if(typeof data15.gap !== "boolean"){
validate38.errors = [{instancePath:instancePath+"/links/" + i3+"/gap",schemaPath:"#/properties/links/items/properties/gap/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid8 = _errs41 === errors;
}
else {
var valid8 = true;
}
}
}
}
}
}
else {
validate38.errors = [{instancePath:instancePath+"/links/" + i3,schemaPath:"#/properties/links/items/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid7 = _errs34 === errors;
if(!valid7){
break;
}
}
}
}
else {
validate38.errors = [{instancePath:instancePath+"/links",schemaPath:"#/properties/links/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs32 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.context !== undefined){
let data19 = data.context;
const _errs43 = errors;
const _errs44 = errors;
if(errors === _errs44){
if(typeof data19 === "string"){
if(func1(data19) > 16384){
validate38.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate38.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs43 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
else {
validate38.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate38.errors = vErrors;
return errors === 0;
}
validate38.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const schema64 = {"type":"object","additionalProperties":false,"minProperties":5,"properties":{"kind":{"const":"inventor-network"},"nodes":{"type":"array","maxItems":40,"items":{"type":"object","additionalProperties":false,"minProperties":7,"properties":{"id":{"$ref":"#/$defs/t"},"label":{"$ref":"#/$defs/t"},"x":{"$ref":"#/$defs/q"},"y":{"$ref":"#/$defs/q"},"value":{"$ref":"#/$defs/u"},"group":{"$ref":"#/$defs/g"},"hop":{"anyOf":[{"type":"integer","minimum":0,"maximum":3},{"type":"null"}]}}}},"edges":{"type":"array","maxItems":300,"items":{"type":"object","additionalProperties":false,"minProperties":5,"properties":{"source":{"$ref":"#/$defs/k"},"target":{"$ref":"#/$defs/k"},"value":{"$ref":"#/$defs/u"},"directed":{"type":"boolean"},"state":{"enum":["observed","inferred","confirmed","corporate"]}}}},"focus":{"anyOf":[{"$ref":"#/$defs/t"},{"type":"null"}]},"context":{"$ref":"#/$defs/c"}}};
const schema67 = {"type":"number","minimum":-1000000000000,"maximum":1000000000000};
const schema69 = {"type":"number","minimum":0,"maximum":1000000000000};
const schema70 = {"type":"integer","minimum":0,"maximum":199};
const schema71 = {"type":"integer","minimum":0,"maximum":499};

function validate40(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate40.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
if(Object.keys(data).length < 5){
validate40.errors = [{instancePath,schemaPath:"#/minProperties",keyword:"minProperties",params:{limit: 5},message:"must NOT have fewer than 5 properties"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!(((((key0 === "kind") || (key0 === "nodes")) || (key0 === "edges")) || (key0 === "focus")) || (key0 === "context"))){
validate40.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.kind !== undefined){
const _errs2 = errors;
if("inventor-network" !== data.kind){
validate40.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/properties/kind/const",keyword:"const",params:{allowedValue: "inventor-network"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.nodes !== undefined){
let data1 = data.nodes;
const _errs3 = errors;
if(errors === _errs3){
if(Array.isArray(data1)){
if(data1.length > 40){
validate40.errors = [{instancePath:instancePath+"/nodes",schemaPath:"#/properties/nodes/maxItems",keyword:"maxItems",params:{limit: 40},message:"must NOT have more than 40 items"}];
return false;
}
else {
var valid1 = true;
const len0 = data1.length;
for(let i0=0; i0<len0; i0++){
let data2 = data1[i0];
const _errs5 = errors;
if(errors === _errs5){
if(data2 && typeof data2 == "object" && !Array.isArray(data2)){
if(Object.keys(data2).length < 7){
validate40.errors = [{instancePath:instancePath+"/nodes/" + i0,schemaPath:"#/properties/nodes/items/minProperties",keyword:"minProperties",params:{limit: 7},message:"must NOT have fewer than 7 properties"}];
return false;
}
else {
const _errs7 = errors;
for(const key1 in data2){
if(!(((((((key1 === "id") || (key1 === "label")) || (key1 === "x")) || (key1 === "y")) || (key1 === "value")) || (key1 === "group")) || (key1 === "hop"))){
validate40.errors = [{instancePath:instancePath+"/nodes/" + i0,schemaPath:"#/properties/nodes/items/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs7 === errors){
if(data2.id !== undefined){
let data3 = data2.id;
const _errs8 = errors;
const _errs9 = errors;
if(errors === _errs9){
if(typeof data3 === "string"){
if(func1(data3) > 4096){
validate40.errors = [{instancePath:instancePath+"/nodes/" + i0+"/id",schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data3) < 1){
validate40.errors = [{instancePath:instancePath+"/nodes/" + i0+"/id",schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate40.errors = [{instancePath:instancePath+"/nodes/" + i0+"/id",schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid2 = _errs8 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data2.label !== undefined){
let data4 = data2.label;
const _errs11 = errors;
const _errs12 = errors;
if(errors === _errs12){
if(typeof data4 === "string"){
if(func1(data4) > 4096){
validate40.errors = [{instancePath:instancePath+"/nodes/" + i0+"/label",schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data4) < 1){
validate40.errors = [{instancePath:instancePath+"/nodes/" + i0+"/label",schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate40.errors = [{instancePath:instancePath+"/nodes/" + i0+"/label",schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid2 = _errs11 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data2.x !== undefined){
let data5 = data2.x;
const _errs14 = errors;
const _errs15 = errors;
if(errors === _errs15){
if((typeof data5 == "number") && (isFinite(data5))){
if(data5 > 1000000000000 || isNaN(data5)){
validate40.errors = [{instancePath:instancePath+"/nodes/" + i0+"/x",schemaPath:"#/$defs/q/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000000000},message:"must be <= 1000000000000"}];
return false;
}
else {
if(data5 < -1000000000000 || isNaN(data5)){
validate40.errors = [{instancePath:instancePath+"/nodes/" + i0+"/x",schemaPath:"#/$defs/q/minimum",keyword:"minimum",params:{comparison: ">=", limit: -1000000000000},message:"must be >= -1000000000000"}];
return false;
}
}
}
else {
validate40.errors = [{instancePath:instancePath+"/nodes/" + i0+"/x",schemaPath:"#/$defs/q/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid2 = _errs14 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data2.y !== undefined){
let data6 = data2.y;
const _errs17 = errors;
const _errs18 = errors;
if(errors === _errs18){
if((typeof data6 == "number") && (isFinite(data6))){
if(data6 > 1000000000000 || isNaN(data6)){
validate40.errors = [{instancePath:instancePath+"/nodes/" + i0+"/y",schemaPath:"#/$defs/q/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000000000},message:"must be <= 1000000000000"}];
return false;
}
else {
if(data6 < -1000000000000 || isNaN(data6)){
validate40.errors = [{instancePath:instancePath+"/nodes/" + i0+"/y",schemaPath:"#/$defs/q/minimum",keyword:"minimum",params:{comparison: ">=", limit: -1000000000000},message:"must be >= -1000000000000"}];
return false;
}
}
}
else {
validate40.errors = [{instancePath:instancePath+"/nodes/" + i0+"/y",schemaPath:"#/$defs/q/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid2 = _errs17 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data2.value !== undefined){
let data7 = data2.value;
const _errs20 = errors;
const _errs21 = errors;
if(errors === _errs21){
if((typeof data7 == "number") && (isFinite(data7))){
if(data7 > 1000000000000 || isNaN(data7)){
validate40.errors = [{instancePath:instancePath+"/nodes/" + i0+"/value",schemaPath:"#/$defs/u/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000000000},message:"must be <= 1000000000000"}];
return false;
}
else {
if(data7 < 0 || isNaN(data7)){
validate40.errors = [{instancePath:instancePath+"/nodes/" + i0+"/value",schemaPath:"#/$defs/u/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
else {
validate40.errors = [{instancePath:instancePath+"/nodes/" + i0+"/value",schemaPath:"#/$defs/u/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid2 = _errs20 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data2.group !== undefined){
let data8 = data2.group;
const _errs23 = errors;
const _errs24 = errors;
if(!(((typeof data8 == "number") && (!(data8 % 1) && !isNaN(data8))) && (isFinite(data8)))){
validate40.errors = [{instancePath:instancePath+"/nodes/" + i0+"/group",schemaPath:"#/$defs/g/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs24){
if((typeof data8 == "number") && (isFinite(data8))){
if(data8 > 199 || isNaN(data8)){
validate40.errors = [{instancePath:instancePath+"/nodes/" + i0+"/group",schemaPath:"#/$defs/g/maximum",keyword:"maximum",params:{comparison: "<=", limit: 199},message:"must be <= 199"}];
return false;
}
else {
if(data8 < 0 || isNaN(data8)){
validate40.errors = [{instancePath:instancePath+"/nodes/" + i0+"/group",schemaPath:"#/$defs/g/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid2 = _errs23 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data2.hop !== undefined){
let data9 = data2.hop;
const _errs26 = errors;
const _errs27 = errors;
let valid9 = false;
const _errs28 = errors;
if(!(((typeof data9 == "number") && (!(data9 % 1) && !isNaN(data9))) && (isFinite(data9)))){
const err0 = {instancePath:instancePath+"/nodes/" + i0+"/hop",schemaPath:"#/properties/nodes/items/properties/hop/anyOf/0/type",keyword:"type",params:{type: "integer"},message:"must be integer"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
if(errors === _errs28){
if((typeof data9 == "number") && (isFinite(data9))){
if(data9 > 3 || isNaN(data9)){
const err1 = {instancePath:instancePath+"/nodes/" + i0+"/hop",schemaPath:"#/properties/nodes/items/properties/hop/anyOf/0/maximum",keyword:"maximum",params:{comparison: "<=", limit: 3},message:"must be <= 3"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
else {
if(data9 < 0 || isNaN(data9)){
const err2 = {instancePath:instancePath+"/nodes/" + i0+"/hop",schemaPath:"#/properties/nodes/items/properties/hop/anyOf/0/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
}
}
}
var _valid0 = _errs28 === errors;
valid9 = valid9 || _valid0;
const _errs30 = errors;
if(data9 !== null){
const err3 = {instancePath:instancePath+"/nodes/" + i0+"/hop",schemaPath:"#/properties/nodes/items/properties/hop/anyOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
var _valid0 = _errs30 === errors;
valid9 = valid9 || _valid0;
if(!valid9){
const err4 = {instancePath:instancePath+"/nodes/" + i0+"/hop",schemaPath:"#/properties/nodes/items/properties/hop/anyOf",keyword:"anyOf",params:{},message:"must match a schema in anyOf"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
validate40.errors = vErrors;
return false;
}
else {
errors = _errs27;
if(vErrors !== null){
if(_errs27){
vErrors.length = _errs27;
}
else {
vErrors = null;
}
}
}
var valid2 = _errs26 === errors;
}
else {
var valid2 = true;
}
}
}
}
}
}
}
}
}
}
else {
validate40.errors = [{instancePath:instancePath+"/nodes/" + i0,schemaPath:"#/properties/nodes/items/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid1 = _errs5 === errors;
if(!valid1){
break;
}
}
}
}
else {
validate40.errors = [{instancePath:instancePath+"/nodes",schemaPath:"#/properties/nodes/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.edges !== undefined){
let data10 = data.edges;
const _errs32 = errors;
if(errors === _errs32){
if(Array.isArray(data10)){
if(data10.length > 300){
validate40.errors = [{instancePath:instancePath+"/edges",schemaPath:"#/properties/edges/maxItems",keyword:"maxItems",params:{limit: 300},message:"must NOT have more than 300 items"}];
return false;
}
else {
var valid10 = true;
const len1 = data10.length;
for(let i1=0; i1<len1; i1++){
let data11 = data10[i1];
const _errs34 = errors;
if(errors === _errs34){
if(data11 && typeof data11 == "object" && !Array.isArray(data11)){
if(Object.keys(data11).length < 5){
validate40.errors = [{instancePath:instancePath+"/edges/" + i1,schemaPath:"#/properties/edges/items/minProperties",keyword:"minProperties",params:{limit: 5},message:"must NOT have fewer than 5 properties"}];
return false;
}
else {
const _errs36 = errors;
for(const key2 in data11){
if(!(((((key2 === "source") || (key2 === "target")) || (key2 === "value")) || (key2 === "directed")) || (key2 === "state"))){
validate40.errors = [{instancePath:instancePath+"/edges/" + i1,schemaPath:"#/properties/edges/items/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key2},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs36 === errors){
if(data11.source !== undefined){
let data12 = data11.source;
const _errs37 = errors;
const _errs38 = errors;
if(!(((typeof data12 == "number") && (!(data12 % 1) && !isNaN(data12))) && (isFinite(data12)))){
validate40.errors = [{instancePath:instancePath+"/edges/" + i1+"/source",schemaPath:"#/$defs/k/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs38){
if((typeof data12 == "number") && (isFinite(data12))){
if(data12 > 499 || isNaN(data12)){
validate40.errors = [{instancePath:instancePath+"/edges/" + i1+"/source",schemaPath:"#/$defs/k/maximum",keyword:"maximum",params:{comparison: "<=", limit: 499},message:"must be <= 499"}];
return false;
}
else {
if(data12 < 0 || isNaN(data12)){
validate40.errors = [{instancePath:instancePath+"/edges/" + i1+"/source",schemaPath:"#/$defs/k/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid11 = _errs37 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data11.target !== undefined){
let data13 = data11.target;
const _errs40 = errors;
const _errs41 = errors;
if(!(((typeof data13 == "number") && (!(data13 % 1) && !isNaN(data13))) && (isFinite(data13)))){
validate40.errors = [{instancePath:instancePath+"/edges/" + i1+"/target",schemaPath:"#/$defs/k/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs41){
if((typeof data13 == "number") && (isFinite(data13))){
if(data13 > 499 || isNaN(data13)){
validate40.errors = [{instancePath:instancePath+"/edges/" + i1+"/target",schemaPath:"#/$defs/k/maximum",keyword:"maximum",params:{comparison: "<=", limit: 499},message:"must be <= 499"}];
return false;
}
else {
if(data13 < 0 || isNaN(data13)){
validate40.errors = [{instancePath:instancePath+"/edges/" + i1+"/target",schemaPath:"#/$defs/k/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid11 = _errs40 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data11.value !== undefined){
let data14 = data11.value;
const _errs43 = errors;
const _errs44 = errors;
if(errors === _errs44){
if((typeof data14 == "number") && (isFinite(data14))){
if(data14 > 1000000000000 || isNaN(data14)){
validate40.errors = [{instancePath:instancePath+"/edges/" + i1+"/value",schemaPath:"#/$defs/u/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000000000},message:"must be <= 1000000000000"}];
return false;
}
else {
if(data14 < 0 || isNaN(data14)){
validate40.errors = [{instancePath:instancePath+"/edges/" + i1+"/value",schemaPath:"#/$defs/u/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
else {
validate40.errors = [{instancePath:instancePath+"/edges/" + i1+"/value",schemaPath:"#/$defs/u/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid11 = _errs43 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data11.directed !== undefined){
const _errs46 = errors;
if(typeof data11.directed !== "boolean"){
validate40.errors = [{instancePath:instancePath+"/edges/" + i1+"/directed",schemaPath:"#/properties/edges/items/properties/directed/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid11 = _errs46 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data11.state !== undefined){
let data16 = data11.state;
const _errs48 = errors;
if(!((((data16 === "observed") || (data16 === "inferred")) || (data16 === "confirmed")) || (data16 === "corporate"))){
validate40.errors = [{instancePath:instancePath+"/edges/" + i1+"/state",schemaPath:"#/properties/edges/items/properties/state/enum",keyword:"enum",params:{allowedValues: schema64.properties.edges.items.properties.state.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid11 = _errs48 === errors;
}
else {
var valid11 = true;
}
}
}
}
}
}
}
}
else {
validate40.errors = [{instancePath:instancePath+"/edges/" + i1,schemaPath:"#/properties/edges/items/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid10 = _errs34 === errors;
if(!valid10){
break;
}
}
}
}
else {
validate40.errors = [{instancePath:instancePath+"/edges",schemaPath:"#/properties/edges/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs32 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.focus !== undefined){
let data17 = data.focus;
const _errs49 = errors;
const _errs50 = errors;
let valid15 = false;
const _errs51 = errors;
const _errs52 = errors;
if(errors === _errs52){
if(typeof data17 === "string"){
if(func1(data17) > 4096){
const err5 = {instancePath:instancePath+"/focus",schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
else {
if(func1(data17) < 1){
const err6 = {instancePath:instancePath+"/focus",schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
}
}
}
else {
const err7 = {instancePath:instancePath+"/focus",schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
}
var _valid1 = _errs51 === errors;
valid15 = valid15 || _valid1;
const _errs54 = errors;
if(data17 !== null){
const err8 = {instancePath:instancePath+"/focus",schemaPath:"#/properties/focus/anyOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
}
var _valid1 = _errs54 === errors;
valid15 = valid15 || _valid1;
if(!valid15){
const err9 = {instancePath:instancePath+"/focus",schemaPath:"#/properties/focus/anyOf",keyword:"anyOf",params:{},message:"must match a schema in anyOf"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
validate40.errors = vErrors;
return false;
}
else {
errors = _errs50;
if(vErrors !== null){
if(_errs50){
vErrors.length = _errs50;
}
else {
vErrors = null;
}
}
}
var valid0 = _errs49 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.context !== undefined){
let data18 = data.context;
const _errs56 = errors;
const _errs57 = errors;
if(errors === _errs57){
if(typeof data18 === "string"){
if(func1(data18) > 16384){
validate40.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate40.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs56 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
else {
validate40.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate40.errors = vErrors;
return errors === 0;
}
validate40.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const schema76 = {"type":"object","additionalProperties":false,"minProperties":8,"properties":{"kind":{"const":"inventor-heatmap"},"x":{"type":"array","maxItems":20,"items":{"$ref":"#/$defs/t"}},"y":{"type":"array","maxItems":20,"items":{"$ref":"#/$defs/t"}},"x_label":{"$ref":"#/$defs/c"},"y_label":{"$ref":"#/$defs/c"},"value_label":{"$ref":"#/$defs/c"},"cells":{"type":"array","maxItems":400,"items":{"type":"object","additionalProperties":false,"minProperties":3,"properties":{"x":{"$ref":"#/$defs/h"},"y":{"$ref":"#/$defs/h"},"value":{"anyOf":[{"$ref":"#/$defs/u"},{"type":"null"}]}}}},"context":{"$ref":"#/$defs/c"}}};
const schema82 = {"type":"integer","minimum":0,"maximum":19};

function validate43(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate43.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
if(Object.keys(data).length < 8){
validate43.errors = [{instancePath,schemaPath:"#/minProperties",keyword:"minProperties",params:{limit: 8},message:"must NOT have fewer than 8 properties"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((((((((key0 === "kind") || (key0 === "x")) || (key0 === "y")) || (key0 === "x_label")) || (key0 === "y_label")) || (key0 === "value_label")) || (key0 === "cells")) || (key0 === "context"))){
validate43.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.kind !== undefined){
const _errs2 = errors;
if("inventor-heatmap" !== data.kind){
validate43.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/properties/kind/const",keyword:"const",params:{allowedValue: "inventor-heatmap"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.x !== undefined){
let data1 = data.x;
const _errs3 = errors;
if(errors === _errs3){
if(Array.isArray(data1)){
if(data1.length > 20){
validate43.errors = [{instancePath:instancePath+"/x",schemaPath:"#/properties/x/maxItems",keyword:"maxItems",params:{limit: 20},message:"must NOT have more than 20 items"}];
return false;
}
else {
var valid1 = true;
const len0 = data1.length;
for(let i0=0; i0<len0; i0++){
let data2 = data1[i0];
const _errs5 = errors;
const _errs6 = errors;
if(errors === _errs6){
if(typeof data2 === "string"){
if(func1(data2) > 4096){
validate43.errors = [{instancePath:instancePath+"/x/" + i0,schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data2) < 1){
validate43.errors = [{instancePath:instancePath+"/x/" + i0,schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate43.errors = [{instancePath:instancePath+"/x/" + i0,schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid1 = _errs5 === errors;
if(!valid1){
break;
}
}
}
}
else {
validate43.errors = [{instancePath:instancePath+"/x",schemaPath:"#/properties/x/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.y !== undefined){
let data3 = data.y;
const _errs8 = errors;
if(errors === _errs8){
if(Array.isArray(data3)){
if(data3.length > 20){
validate43.errors = [{instancePath:instancePath+"/y",schemaPath:"#/properties/y/maxItems",keyword:"maxItems",params:{limit: 20},message:"must NOT have more than 20 items"}];
return false;
}
else {
var valid3 = true;
const len1 = data3.length;
for(let i1=0; i1<len1; i1++){
let data4 = data3[i1];
const _errs10 = errors;
const _errs11 = errors;
if(errors === _errs11){
if(typeof data4 === "string"){
if(func1(data4) > 4096){
validate43.errors = [{instancePath:instancePath+"/y/" + i1,schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data4) < 1){
validate43.errors = [{instancePath:instancePath+"/y/" + i1,schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate43.errors = [{instancePath:instancePath+"/y/" + i1,schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid3 = _errs10 === errors;
if(!valid3){
break;
}
}
}
}
else {
validate43.errors = [{instancePath:instancePath+"/y",schemaPath:"#/properties/y/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs8 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.x_label !== undefined){
let data5 = data.x_label;
const _errs13 = errors;
const _errs14 = errors;
if(errors === _errs14){
if(typeof data5 === "string"){
if(func1(data5) > 16384){
validate43.errors = [{instancePath:instancePath+"/x_label",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate43.errors = [{instancePath:instancePath+"/x_label",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs13 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.y_label !== undefined){
let data6 = data.y_label;
const _errs16 = errors;
const _errs17 = errors;
if(errors === _errs17){
if(typeof data6 === "string"){
if(func1(data6) > 16384){
validate43.errors = [{instancePath:instancePath+"/y_label",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate43.errors = [{instancePath:instancePath+"/y_label",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs16 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.value_label !== undefined){
let data7 = data.value_label;
const _errs19 = errors;
const _errs20 = errors;
if(errors === _errs20){
if(typeof data7 === "string"){
if(func1(data7) > 16384){
validate43.errors = [{instancePath:instancePath+"/value_label",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate43.errors = [{instancePath:instancePath+"/value_label",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs19 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.cells !== undefined){
let data8 = data.cells;
const _errs22 = errors;
if(errors === _errs22){
if(Array.isArray(data8)){
if(data8.length > 400){
validate43.errors = [{instancePath:instancePath+"/cells",schemaPath:"#/properties/cells/maxItems",keyword:"maxItems",params:{limit: 400},message:"must NOT have more than 400 items"}];
return false;
}
else {
var valid8 = true;
const len2 = data8.length;
for(let i2=0; i2<len2; i2++){
let data9 = data8[i2];
const _errs24 = errors;
if(errors === _errs24){
if(data9 && typeof data9 == "object" && !Array.isArray(data9)){
if(Object.keys(data9).length < 3){
validate43.errors = [{instancePath:instancePath+"/cells/" + i2,schemaPath:"#/properties/cells/items/minProperties",keyword:"minProperties",params:{limit: 3},message:"must NOT have fewer than 3 properties"}];
return false;
}
else {
const _errs26 = errors;
for(const key1 in data9){
if(!(((key1 === "x") || (key1 === "y")) || (key1 === "value"))){
validate43.errors = [{instancePath:instancePath+"/cells/" + i2,schemaPath:"#/properties/cells/items/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs26 === errors){
if(data9.x !== undefined){
let data10 = data9.x;
const _errs27 = errors;
const _errs28 = errors;
if(!(((typeof data10 == "number") && (!(data10 % 1) && !isNaN(data10))) && (isFinite(data10)))){
validate43.errors = [{instancePath:instancePath+"/cells/" + i2+"/x",schemaPath:"#/$defs/h/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs28){
if((typeof data10 == "number") && (isFinite(data10))){
if(data10 > 19 || isNaN(data10)){
validate43.errors = [{instancePath:instancePath+"/cells/" + i2+"/x",schemaPath:"#/$defs/h/maximum",keyword:"maximum",params:{comparison: "<=", limit: 19},message:"must be <= 19"}];
return false;
}
else {
if(data10 < 0 || isNaN(data10)){
validate43.errors = [{instancePath:instancePath+"/cells/" + i2+"/x",schemaPath:"#/$defs/h/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid9 = _errs27 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data9.y !== undefined){
let data11 = data9.y;
const _errs30 = errors;
const _errs31 = errors;
if(!(((typeof data11 == "number") && (!(data11 % 1) && !isNaN(data11))) && (isFinite(data11)))){
validate43.errors = [{instancePath:instancePath+"/cells/" + i2+"/y",schemaPath:"#/$defs/h/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs31){
if((typeof data11 == "number") && (isFinite(data11))){
if(data11 > 19 || isNaN(data11)){
validate43.errors = [{instancePath:instancePath+"/cells/" + i2+"/y",schemaPath:"#/$defs/h/maximum",keyword:"maximum",params:{comparison: "<=", limit: 19},message:"must be <= 19"}];
return false;
}
else {
if(data11 < 0 || isNaN(data11)){
validate43.errors = [{instancePath:instancePath+"/cells/" + i2+"/y",schemaPath:"#/$defs/h/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid9 = _errs30 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data9.value !== undefined){
let data12 = data9.value;
const _errs33 = errors;
const _errs34 = errors;
let valid12 = false;
const _errs35 = errors;
const _errs36 = errors;
if(errors === _errs36){
if((typeof data12 == "number") && (isFinite(data12))){
if(data12 > 1000000000000 || isNaN(data12)){
const err0 = {instancePath:instancePath+"/cells/" + i2+"/value",schemaPath:"#/$defs/u/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000000000},message:"must be <= 1000000000000"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
else {
if(data12 < 0 || isNaN(data12)){
const err1 = {instancePath:instancePath+"/cells/" + i2+"/value",schemaPath:"#/$defs/u/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
}
}
else {
const err2 = {instancePath:instancePath+"/cells/" + i2+"/value",schemaPath:"#/$defs/u/type",keyword:"type",params:{type: "number"},message:"must be number"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
}
var _valid0 = _errs35 === errors;
valid12 = valid12 || _valid0;
const _errs38 = errors;
if(data12 !== null){
const err3 = {instancePath:instancePath+"/cells/" + i2+"/value",schemaPath:"#/properties/cells/items/properties/value/anyOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
var _valid0 = _errs38 === errors;
valid12 = valid12 || _valid0;
if(!valid12){
const err4 = {instancePath:instancePath+"/cells/" + i2+"/value",schemaPath:"#/properties/cells/items/properties/value/anyOf",keyword:"anyOf",params:{},message:"must match a schema in anyOf"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
validate43.errors = vErrors;
return false;
}
else {
errors = _errs34;
if(vErrors !== null){
if(_errs34){
vErrors.length = _errs34;
}
else {
vErrors = null;
}
}
}
var valid9 = _errs33 === errors;
}
else {
var valid9 = true;
}
}
}
}
}
}
else {
validate43.errors = [{instancePath:instancePath+"/cells/" + i2,schemaPath:"#/properties/cells/items/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid8 = _errs24 === errors;
if(!valid8){
break;
}
}
}
}
else {
validate43.errors = [{instancePath:instancePath+"/cells",schemaPath:"#/properties/cells/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs22 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.context !== undefined){
let data13 = data.context;
const _errs40 = errors;
const _errs41 = errors;
if(errors === _errs41){
if(typeof data13 === "string"){
if(func1(data13) > 16384){
validate43.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate43.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs40 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
validate43.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate43.errors = vErrors;
return errors === 0;
}
validate43.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const schema86 = {"type":"object","additionalProperties":false,"minProperties":7,"properties":{"kind":{"const":"inventor-timeline"},"lanes":{"type":"array","maxItems":20,"items":{"$ref":"#/$defs/t"}},"years":{"type":"array","maxItems":30,"items":{"$ref":"#/$defs/y"}},"nodes":{"type":"array","maxItems":500,"items":{"type":"object","additionalProperties":false,"minProperties":7,"properties":{"id":{"$ref":"#/$defs/t"},"x":{"$ref":"#/$defs/r"},"y":{"$ref":"#/$defs/h"},"size":{"$ref":"#/$defs/u"},"category":{"$ref":"#/$defs/g"},"label":{"$ref":"#/$defs/t"},"state":{"enum":["observed","inferred","confirmed","unknown"]}}}},"links":{"type":"array","maxItems":500,"items":{"type":"object","additionalProperties":false,"minProperties":4,"properties":{"source":{"$ref":"#/$defs/k"},"target":{"$ref":"#/$defs/k"},"gap":{"type":"boolean"},"state":{"$ref":"#/$defs/s"}}}},"bands":{"type":"array","maxItems":100,"items":{"type":"object","additionalProperties":false,"minProperties":6,"properties":{"id":{"$ref":"#/$defs/t"},"start":{"$ref":"#/$defs/r"},"end":{"$ref":"#/$defs/r"},"label":{"$ref":"#/$defs/t"},"kind":{"enum":["acquisition","merger","name_change","group_change","rights_transfer","organizational_transfer"]},"status":{"enum":["announced","completed"]}}}},"context":{"$ref":"#/$defs/c"}}};
const schema88 = {"type":"integer","minimum":1800,"maximum":2199};
const schema90 = {"type":"number","minimum":1800,"maximum":2200};
const schema97 = {"enum":["observed","inferred","confirmed"]};

function validate45(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate45.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
if(Object.keys(data).length < 7){
validate45.errors = [{instancePath,schemaPath:"#/minProperties",keyword:"minProperties",params:{limit: 7},message:"must NOT have fewer than 7 properties"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!(((((((key0 === "kind") || (key0 === "lanes")) || (key0 === "years")) || (key0 === "nodes")) || (key0 === "links")) || (key0 === "bands")) || (key0 === "context"))){
validate45.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.kind !== undefined){
const _errs2 = errors;
if("inventor-timeline" !== data.kind){
validate45.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/properties/kind/const",keyword:"const",params:{allowedValue: "inventor-timeline"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.lanes !== undefined){
let data1 = data.lanes;
const _errs3 = errors;
if(errors === _errs3){
if(Array.isArray(data1)){
if(data1.length > 20){
validate45.errors = [{instancePath:instancePath+"/lanes",schemaPath:"#/properties/lanes/maxItems",keyword:"maxItems",params:{limit: 20},message:"must NOT have more than 20 items"}];
return false;
}
else {
var valid1 = true;
const len0 = data1.length;
for(let i0=0; i0<len0; i0++){
let data2 = data1[i0];
const _errs5 = errors;
const _errs6 = errors;
if(errors === _errs6){
if(typeof data2 === "string"){
if(func1(data2) > 4096){
validate45.errors = [{instancePath:instancePath+"/lanes/" + i0,schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data2) < 1){
validate45.errors = [{instancePath:instancePath+"/lanes/" + i0,schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate45.errors = [{instancePath:instancePath+"/lanes/" + i0,schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid1 = _errs5 === errors;
if(!valid1){
break;
}
}
}
}
else {
validate45.errors = [{instancePath:instancePath+"/lanes",schemaPath:"#/properties/lanes/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.years !== undefined){
let data3 = data.years;
const _errs8 = errors;
if(errors === _errs8){
if(Array.isArray(data3)){
if(data3.length > 30){
validate45.errors = [{instancePath:instancePath+"/years",schemaPath:"#/properties/years/maxItems",keyword:"maxItems",params:{limit: 30},message:"must NOT have more than 30 items"}];
return false;
}
else {
var valid3 = true;
const len1 = data3.length;
for(let i1=0; i1<len1; i1++){
let data4 = data3[i1];
const _errs10 = errors;
const _errs11 = errors;
if(!(((typeof data4 == "number") && (!(data4 % 1) && !isNaN(data4))) && (isFinite(data4)))){
validate45.errors = [{instancePath:instancePath+"/years/" + i1,schemaPath:"#/$defs/y/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs11){
if((typeof data4 == "number") && (isFinite(data4))){
if(data4 > 2199 || isNaN(data4)){
validate45.errors = [{instancePath:instancePath+"/years/" + i1,schemaPath:"#/$defs/y/maximum",keyword:"maximum",params:{comparison: "<=", limit: 2199},message:"must be <= 2199"}];
return false;
}
else {
if(data4 < 1800 || isNaN(data4)){
validate45.errors = [{instancePath:instancePath+"/years/" + i1,schemaPath:"#/$defs/y/minimum",keyword:"minimum",params:{comparison: ">=", limit: 1800},message:"must be >= 1800"}];
return false;
}
}
}
}
var valid3 = _errs10 === errors;
if(!valid3){
break;
}
}
}
}
else {
validate45.errors = [{instancePath:instancePath+"/years",schemaPath:"#/properties/years/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs8 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.nodes !== undefined){
let data5 = data.nodes;
const _errs13 = errors;
if(errors === _errs13){
if(Array.isArray(data5)){
if(data5.length > 500){
validate45.errors = [{instancePath:instancePath+"/nodes",schemaPath:"#/properties/nodes/maxItems",keyword:"maxItems",params:{limit: 500},message:"must NOT have more than 500 items"}];
return false;
}
else {
var valid5 = true;
const len2 = data5.length;
for(let i2=0; i2<len2; i2++){
let data6 = data5[i2];
const _errs15 = errors;
if(errors === _errs15){
if(data6 && typeof data6 == "object" && !Array.isArray(data6)){
if(Object.keys(data6).length < 7){
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2,schemaPath:"#/properties/nodes/items/minProperties",keyword:"minProperties",params:{limit: 7},message:"must NOT have fewer than 7 properties"}];
return false;
}
else {
const _errs17 = errors;
for(const key1 in data6){
if(!(((((((key1 === "id") || (key1 === "x")) || (key1 === "y")) || (key1 === "size")) || (key1 === "category")) || (key1 === "label")) || (key1 === "state"))){
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2,schemaPath:"#/properties/nodes/items/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs17 === errors){
if(data6.id !== undefined){
let data7 = data6.id;
const _errs18 = errors;
const _errs19 = errors;
if(errors === _errs19){
if(typeof data7 === "string"){
if(func1(data7) > 4096){
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2+"/id",schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data7) < 1){
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2+"/id",schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2+"/id",schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid6 = _errs18 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.x !== undefined){
let data8 = data6.x;
const _errs21 = errors;
const _errs22 = errors;
if(errors === _errs22){
if((typeof data8 == "number") && (isFinite(data8))){
if(data8 > 2200 || isNaN(data8)){
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2+"/x",schemaPath:"#/$defs/r/maximum",keyword:"maximum",params:{comparison: "<=", limit: 2200},message:"must be <= 2200"}];
return false;
}
else {
if(data8 < 1800 || isNaN(data8)){
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2+"/x",schemaPath:"#/$defs/r/minimum",keyword:"minimum",params:{comparison: ">=", limit: 1800},message:"must be >= 1800"}];
return false;
}
}
}
else {
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2+"/x",schemaPath:"#/$defs/r/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid6 = _errs21 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.y !== undefined){
let data9 = data6.y;
const _errs24 = errors;
const _errs25 = errors;
if(!(((typeof data9 == "number") && (!(data9 % 1) && !isNaN(data9))) && (isFinite(data9)))){
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2+"/y",schemaPath:"#/$defs/h/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs25){
if((typeof data9 == "number") && (isFinite(data9))){
if(data9 > 19 || isNaN(data9)){
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2+"/y",schemaPath:"#/$defs/h/maximum",keyword:"maximum",params:{comparison: "<=", limit: 19},message:"must be <= 19"}];
return false;
}
else {
if(data9 < 0 || isNaN(data9)){
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2+"/y",schemaPath:"#/$defs/h/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid6 = _errs24 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.size !== undefined){
let data10 = data6.size;
const _errs27 = errors;
const _errs28 = errors;
if(errors === _errs28){
if((typeof data10 == "number") && (isFinite(data10))){
if(data10 > 1000000000000 || isNaN(data10)){
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2+"/size",schemaPath:"#/$defs/u/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000000000},message:"must be <= 1000000000000"}];
return false;
}
else {
if(data10 < 0 || isNaN(data10)){
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2+"/size",schemaPath:"#/$defs/u/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
else {
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2+"/size",schemaPath:"#/$defs/u/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid6 = _errs27 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.category !== undefined){
let data11 = data6.category;
const _errs30 = errors;
const _errs31 = errors;
if(!(((typeof data11 == "number") && (!(data11 % 1) && !isNaN(data11))) && (isFinite(data11)))){
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2+"/category",schemaPath:"#/$defs/g/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs31){
if((typeof data11 == "number") && (isFinite(data11))){
if(data11 > 199 || isNaN(data11)){
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2+"/category",schemaPath:"#/$defs/g/maximum",keyword:"maximum",params:{comparison: "<=", limit: 199},message:"must be <= 199"}];
return false;
}
else {
if(data11 < 0 || isNaN(data11)){
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2+"/category",schemaPath:"#/$defs/g/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid6 = _errs30 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.label !== undefined){
let data12 = data6.label;
const _errs33 = errors;
const _errs34 = errors;
if(errors === _errs34){
if(typeof data12 === "string"){
if(func1(data12) > 4096){
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2+"/label",schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data12) < 1){
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2+"/label",schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2+"/label",schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid6 = _errs33 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data6.state !== undefined){
let data13 = data6.state;
const _errs36 = errors;
if(!((((data13 === "observed") || (data13 === "inferred")) || (data13 === "confirmed")) || (data13 === "unknown"))){
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2+"/state",schemaPath:"#/properties/nodes/items/properties/state/enum",keyword:"enum",params:{allowedValues: schema86.properties.nodes.items.properties.state.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid6 = _errs36 === errors;
}
else {
var valid6 = true;
}
}
}
}
}
}
}
}
}
}
else {
validate45.errors = [{instancePath:instancePath+"/nodes/" + i2,schemaPath:"#/properties/nodes/items/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid5 = _errs15 === errors;
if(!valid5){
break;
}
}
}
}
else {
validate45.errors = [{instancePath:instancePath+"/nodes",schemaPath:"#/properties/nodes/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs13 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.links !== undefined){
let data14 = data.links;
const _errs37 = errors;
if(errors === _errs37){
if(Array.isArray(data14)){
if(data14.length > 500){
validate45.errors = [{instancePath:instancePath+"/links",schemaPath:"#/properties/links/maxItems",keyword:"maxItems",params:{limit: 500},message:"must NOT have more than 500 items"}];
return false;
}
else {
var valid13 = true;
const len3 = data14.length;
for(let i3=0; i3<len3; i3++){
let data15 = data14[i3];
const _errs39 = errors;
if(errors === _errs39){
if(data15 && typeof data15 == "object" && !Array.isArray(data15)){
if(Object.keys(data15).length < 4){
validate45.errors = [{instancePath:instancePath+"/links/" + i3,schemaPath:"#/properties/links/items/minProperties",keyword:"minProperties",params:{limit: 4},message:"must NOT have fewer than 4 properties"}];
return false;
}
else {
const _errs41 = errors;
for(const key2 in data15){
if(!((((key2 === "source") || (key2 === "target")) || (key2 === "gap")) || (key2 === "state"))){
validate45.errors = [{instancePath:instancePath+"/links/" + i3,schemaPath:"#/properties/links/items/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key2},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs41 === errors){
if(data15.source !== undefined){
let data16 = data15.source;
const _errs42 = errors;
const _errs43 = errors;
if(!(((typeof data16 == "number") && (!(data16 % 1) && !isNaN(data16))) && (isFinite(data16)))){
validate45.errors = [{instancePath:instancePath+"/links/" + i3+"/source",schemaPath:"#/$defs/k/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs43){
if((typeof data16 == "number") && (isFinite(data16))){
if(data16 > 499 || isNaN(data16)){
validate45.errors = [{instancePath:instancePath+"/links/" + i3+"/source",schemaPath:"#/$defs/k/maximum",keyword:"maximum",params:{comparison: "<=", limit: 499},message:"must be <= 499"}];
return false;
}
else {
if(data16 < 0 || isNaN(data16)){
validate45.errors = [{instancePath:instancePath+"/links/" + i3+"/source",schemaPath:"#/$defs/k/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid14 = _errs42 === errors;
}
else {
var valid14 = true;
}
if(valid14){
if(data15.target !== undefined){
let data17 = data15.target;
const _errs45 = errors;
const _errs46 = errors;
if(!(((typeof data17 == "number") && (!(data17 % 1) && !isNaN(data17))) && (isFinite(data17)))){
validate45.errors = [{instancePath:instancePath+"/links/" + i3+"/target",schemaPath:"#/$defs/k/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs46){
if((typeof data17 == "number") && (isFinite(data17))){
if(data17 > 499 || isNaN(data17)){
validate45.errors = [{instancePath:instancePath+"/links/" + i3+"/target",schemaPath:"#/$defs/k/maximum",keyword:"maximum",params:{comparison: "<=", limit: 499},message:"must be <= 499"}];
return false;
}
else {
if(data17 < 0 || isNaN(data17)){
validate45.errors = [{instancePath:instancePath+"/links/" + i3+"/target",schemaPath:"#/$defs/k/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid14 = _errs45 === errors;
}
else {
var valid14 = true;
}
if(valid14){
if(data15.gap !== undefined){
const _errs48 = errors;
if(typeof data15.gap !== "boolean"){
validate45.errors = [{instancePath:instancePath+"/links/" + i3+"/gap",schemaPath:"#/properties/links/items/properties/gap/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid14 = _errs48 === errors;
}
else {
var valid14 = true;
}
if(valid14){
if(data15.state !== undefined){
let data19 = data15.state;
const _errs50 = errors;
if(!(((data19 === "observed") || (data19 === "inferred")) || (data19 === "confirmed"))){
validate45.errors = [{instancePath:instancePath+"/links/" + i3+"/state",schemaPath:"#/$defs/s/enum",keyword:"enum",params:{allowedValues: schema97.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid14 = _errs50 === errors;
}
else {
var valid14 = true;
}
}
}
}
}
}
}
else {
validate45.errors = [{instancePath:instancePath+"/links/" + i3,schemaPath:"#/properties/links/items/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid13 = _errs39 === errors;
if(!valid13){
break;
}
}
}
}
else {
validate45.errors = [{instancePath:instancePath+"/links",schemaPath:"#/properties/links/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs37 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.bands !== undefined){
let data20 = data.bands;
const _errs52 = errors;
if(errors === _errs52){
if(Array.isArray(data20)){
if(data20.length > 100){
validate45.errors = [{instancePath:instancePath+"/bands",schemaPath:"#/properties/bands/maxItems",keyword:"maxItems",params:{limit: 100},message:"must NOT have more than 100 items"}];
return false;
}
else {
var valid18 = true;
const len4 = data20.length;
for(let i4=0; i4<len4; i4++){
let data21 = data20[i4];
const _errs54 = errors;
if(errors === _errs54){
if(data21 && typeof data21 == "object" && !Array.isArray(data21)){
if(Object.keys(data21).length < 6){
validate45.errors = [{instancePath:instancePath+"/bands/" + i4,schemaPath:"#/properties/bands/items/minProperties",keyword:"minProperties",params:{limit: 6},message:"must NOT have fewer than 6 properties"}];
return false;
}
else {
const _errs56 = errors;
for(const key3 in data21){
if(!((((((key3 === "id") || (key3 === "start")) || (key3 === "end")) || (key3 === "label")) || (key3 === "kind")) || (key3 === "status"))){
validate45.errors = [{instancePath:instancePath+"/bands/" + i4,schemaPath:"#/properties/bands/items/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key3},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs56 === errors){
if(data21.id !== undefined){
let data22 = data21.id;
const _errs57 = errors;
const _errs58 = errors;
if(errors === _errs58){
if(typeof data22 === "string"){
if(func1(data22) > 4096){
validate45.errors = [{instancePath:instancePath+"/bands/" + i4+"/id",schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data22) < 1){
validate45.errors = [{instancePath:instancePath+"/bands/" + i4+"/id",schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate45.errors = [{instancePath:instancePath+"/bands/" + i4+"/id",schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid19 = _errs57 === errors;
}
else {
var valid19 = true;
}
if(valid19){
if(data21.start !== undefined){
let data23 = data21.start;
const _errs60 = errors;
const _errs61 = errors;
if(errors === _errs61){
if((typeof data23 == "number") && (isFinite(data23))){
if(data23 > 2200 || isNaN(data23)){
validate45.errors = [{instancePath:instancePath+"/bands/" + i4+"/start",schemaPath:"#/$defs/r/maximum",keyword:"maximum",params:{comparison: "<=", limit: 2200},message:"must be <= 2200"}];
return false;
}
else {
if(data23 < 1800 || isNaN(data23)){
validate45.errors = [{instancePath:instancePath+"/bands/" + i4+"/start",schemaPath:"#/$defs/r/minimum",keyword:"minimum",params:{comparison: ">=", limit: 1800},message:"must be >= 1800"}];
return false;
}
}
}
else {
validate45.errors = [{instancePath:instancePath+"/bands/" + i4+"/start",schemaPath:"#/$defs/r/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid19 = _errs60 === errors;
}
else {
var valid19 = true;
}
if(valid19){
if(data21.end !== undefined){
let data24 = data21.end;
const _errs63 = errors;
const _errs64 = errors;
if(errors === _errs64){
if((typeof data24 == "number") && (isFinite(data24))){
if(data24 > 2200 || isNaN(data24)){
validate45.errors = [{instancePath:instancePath+"/bands/" + i4+"/end",schemaPath:"#/$defs/r/maximum",keyword:"maximum",params:{comparison: "<=", limit: 2200},message:"must be <= 2200"}];
return false;
}
else {
if(data24 < 1800 || isNaN(data24)){
validate45.errors = [{instancePath:instancePath+"/bands/" + i4+"/end",schemaPath:"#/$defs/r/minimum",keyword:"minimum",params:{comparison: ">=", limit: 1800},message:"must be >= 1800"}];
return false;
}
}
}
else {
validate45.errors = [{instancePath:instancePath+"/bands/" + i4+"/end",schemaPath:"#/$defs/r/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid19 = _errs63 === errors;
}
else {
var valid19 = true;
}
if(valid19){
if(data21.label !== undefined){
let data25 = data21.label;
const _errs66 = errors;
const _errs67 = errors;
if(errors === _errs67){
if(typeof data25 === "string"){
if(func1(data25) > 4096){
validate45.errors = [{instancePath:instancePath+"/bands/" + i4+"/label",schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data25) < 1){
validate45.errors = [{instancePath:instancePath+"/bands/" + i4+"/label",schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate45.errors = [{instancePath:instancePath+"/bands/" + i4+"/label",schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid19 = _errs66 === errors;
}
else {
var valid19 = true;
}
if(valid19){
if(data21.kind !== undefined){
let data26 = data21.kind;
const _errs69 = errors;
if(!((((((data26 === "acquisition") || (data26 === "merger")) || (data26 === "name_change")) || (data26 === "group_change")) || (data26 === "rights_transfer")) || (data26 === "organizational_transfer"))){
validate45.errors = [{instancePath:instancePath+"/bands/" + i4+"/kind",schemaPath:"#/properties/bands/items/properties/kind/enum",keyword:"enum",params:{allowedValues: schema86.properties.bands.items.properties.kind.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid19 = _errs69 === errors;
}
else {
var valid19 = true;
}
if(valid19){
if(data21.status !== undefined){
let data27 = data21.status;
const _errs70 = errors;
if(!((data27 === "announced") || (data27 === "completed"))){
validate45.errors = [{instancePath:instancePath+"/bands/" + i4+"/status",schemaPath:"#/properties/bands/items/properties/status/enum",keyword:"enum",params:{allowedValues: schema86.properties.bands.items.properties.status.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid19 = _errs70 === errors;
}
else {
var valid19 = true;
}
}
}
}
}
}
}
}
}
else {
validate45.errors = [{instancePath:instancePath+"/bands/" + i4,schemaPath:"#/properties/bands/items/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid18 = _errs54 === errors;
if(!valid18){
break;
}
}
}
}
else {
validate45.errors = [{instancePath:instancePath+"/bands",schemaPath:"#/properties/bands/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs52 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.context !== undefined){
let data28 = data.context;
const _errs71 = errors;
const _errs72 = errors;
if(errors === _errs72){
if(typeof data28 === "string"){
if(func1(data28) > 16384){
validate45.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate45.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs71 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
else {
validate45.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate45.errors = vErrors;
return errors === 0;
}
validate45.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const schema103 = {"type":"object","additionalProperties":false,"minProperties":5,"properties":{"kind":{"const":"inventor-alluvial"},"years":{"type":"array","maxItems":30,"items":{"$ref":"#/$defs/y"}},"nodes":{"type":"array","maxItems":100,"items":{"type":"object","additionalProperties":false,"minProperties":5,"properties":{"id":{"$ref":"#/$defs/t"},"label":{"$ref":"#/$defs/t"},"year":{"$ref":"#/$defs/y"},"members":{"type":"integer","minimum":0,"maximum":1000000},"kind":{"enum":["cluster","newly_observed","not_observed"]}}}},"links":{"type":"array","maxItems":300,"items":{"type":"object","additionalProperties":false,"minProperties":4,"properties":{"source":{"$ref":"#/$defs/k"},"target":{"$ref":"#/$defs/k"},"value":{"type":"integer","minimum":1,"maximum":1000000},"kind":{"enum":["continuation","split","merge","gap","newly_observed","not_observed"]}}}},"context":{"$ref":"#/$defs/c"}}};

function validate47(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate47.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
if(Object.keys(data).length < 5){
validate47.errors = [{instancePath,schemaPath:"#/minProperties",keyword:"minProperties",params:{limit: 5},message:"must NOT have fewer than 5 properties"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!(((((key0 === "kind") || (key0 === "years")) || (key0 === "nodes")) || (key0 === "links")) || (key0 === "context"))){
validate47.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.kind !== undefined){
const _errs2 = errors;
if("inventor-alluvial" !== data.kind){
validate47.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/properties/kind/const",keyword:"const",params:{allowedValue: "inventor-alluvial"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.years !== undefined){
let data1 = data.years;
const _errs3 = errors;
if(errors === _errs3){
if(Array.isArray(data1)){
if(data1.length > 30){
validate47.errors = [{instancePath:instancePath+"/years",schemaPath:"#/properties/years/maxItems",keyword:"maxItems",params:{limit: 30},message:"must NOT have more than 30 items"}];
return false;
}
else {
var valid1 = true;
const len0 = data1.length;
for(let i0=0; i0<len0; i0++){
let data2 = data1[i0];
const _errs5 = errors;
const _errs6 = errors;
if(!(((typeof data2 == "number") && (!(data2 % 1) && !isNaN(data2))) && (isFinite(data2)))){
validate47.errors = [{instancePath:instancePath+"/years/" + i0,schemaPath:"#/$defs/y/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs6){
if((typeof data2 == "number") && (isFinite(data2))){
if(data2 > 2199 || isNaN(data2)){
validate47.errors = [{instancePath:instancePath+"/years/" + i0,schemaPath:"#/$defs/y/maximum",keyword:"maximum",params:{comparison: "<=", limit: 2199},message:"must be <= 2199"}];
return false;
}
else {
if(data2 < 1800 || isNaN(data2)){
validate47.errors = [{instancePath:instancePath+"/years/" + i0,schemaPath:"#/$defs/y/minimum",keyword:"minimum",params:{comparison: ">=", limit: 1800},message:"must be >= 1800"}];
return false;
}
}
}
}
var valid1 = _errs5 === errors;
if(!valid1){
break;
}
}
}
}
else {
validate47.errors = [{instancePath:instancePath+"/years",schemaPath:"#/properties/years/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.nodes !== undefined){
let data3 = data.nodes;
const _errs8 = errors;
if(errors === _errs8){
if(Array.isArray(data3)){
if(data3.length > 100){
validate47.errors = [{instancePath:instancePath+"/nodes",schemaPath:"#/properties/nodes/maxItems",keyword:"maxItems",params:{limit: 100},message:"must NOT have more than 100 items"}];
return false;
}
else {
var valid3 = true;
const len1 = data3.length;
for(let i1=0; i1<len1; i1++){
let data4 = data3[i1];
const _errs10 = errors;
if(errors === _errs10){
if(data4 && typeof data4 == "object" && !Array.isArray(data4)){
if(Object.keys(data4).length < 5){
validate47.errors = [{instancePath:instancePath+"/nodes/" + i1,schemaPath:"#/properties/nodes/items/minProperties",keyword:"minProperties",params:{limit: 5},message:"must NOT have fewer than 5 properties"}];
return false;
}
else {
const _errs12 = errors;
for(const key1 in data4){
if(!(((((key1 === "id") || (key1 === "label")) || (key1 === "year")) || (key1 === "members")) || (key1 === "kind"))){
validate47.errors = [{instancePath:instancePath+"/nodes/" + i1,schemaPath:"#/properties/nodes/items/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs12 === errors){
if(data4.id !== undefined){
let data5 = data4.id;
const _errs13 = errors;
const _errs14 = errors;
if(errors === _errs14){
if(typeof data5 === "string"){
if(func1(data5) > 4096){
validate47.errors = [{instancePath:instancePath+"/nodes/" + i1+"/id",schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data5) < 1){
validate47.errors = [{instancePath:instancePath+"/nodes/" + i1+"/id",schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate47.errors = [{instancePath:instancePath+"/nodes/" + i1+"/id",schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid4 = _errs13 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data4.label !== undefined){
let data6 = data4.label;
const _errs16 = errors;
const _errs17 = errors;
if(errors === _errs17){
if(typeof data6 === "string"){
if(func1(data6) > 4096){
validate47.errors = [{instancePath:instancePath+"/nodes/" + i1+"/label",schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data6) < 1){
validate47.errors = [{instancePath:instancePath+"/nodes/" + i1+"/label",schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate47.errors = [{instancePath:instancePath+"/nodes/" + i1+"/label",schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid4 = _errs16 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data4.year !== undefined){
let data7 = data4.year;
const _errs19 = errors;
const _errs20 = errors;
if(!(((typeof data7 == "number") && (!(data7 % 1) && !isNaN(data7))) && (isFinite(data7)))){
validate47.errors = [{instancePath:instancePath+"/nodes/" + i1+"/year",schemaPath:"#/$defs/y/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs20){
if((typeof data7 == "number") && (isFinite(data7))){
if(data7 > 2199 || isNaN(data7)){
validate47.errors = [{instancePath:instancePath+"/nodes/" + i1+"/year",schemaPath:"#/$defs/y/maximum",keyword:"maximum",params:{comparison: "<=", limit: 2199},message:"must be <= 2199"}];
return false;
}
else {
if(data7 < 1800 || isNaN(data7)){
validate47.errors = [{instancePath:instancePath+"/nodes/" + i1+"/year",schemaPath:"#/$defs/y/minimum",keyword:"minimum",params:{comparison: ">=", limit: 1800},message:"must be >= 1800"}];
return false;
}
}
}
}
var valid4 = _errs19 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data4.members !== undefined){
let data8 = data4.members;
const _errs22 = errors;
if(!(((typeof data8 == "number") && (!(data8 % 1) && !isNaN(data8))) && (isFinite(data8)))){
validate47.errors = [{instancePath:instancePath+"/nodes/" + i1+"/members",schemaPath:"#/properties/nodes/items/properties/members/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs22){
if((typeof data8 == "number") && (isFinite(data8))){
if(data8 > 1000000 || isNaN(data8)){
validate47.errors = [{instancePath:instancePath+"/nodes/" + i1+"/members",schemaPath:"#/properties/nodes/items/properties/members/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000},message:"must be <= 1000000"}];
return false;
}
else {
if(data8 < 0 || isNaN(data8)){
validate47.errors = [{instancePath:instancePath+"/nodes/" + i1+"/members",schemaPath:"#/properties/nodes/items/properties/members/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid4 = _errs22 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data4.kind !== undefined){
let data9 = data4.kind;
const _errs24 = errors;
if(!(((data9 === "cluster") || (data9 === "newly_observed")) || (data9 === "not_observed"))){
validate47.errors = [{instancePath:instancePath+"/nodes/" + i1+"/kind",schemaPath:"#/properties/nodes/items/properties/kind/enum",keyword:"enum",params:{allowedValues: schema103.properties.nodes.items.properties.kind.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid4 = _errs24 === errors;
}
else {
var valid4 = true;
}
}
}
}
}
}
}
}
else {
validate47.errors = [{instancePath:instancePath+"/nodes/" + i1,schemaPath:"#/properties/nodes/items/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid3 = _errs10 === errors;
if(!valid3){
break;
}
}
}
}
else {
validate47.errors = [{instancePath:instancePath+"/nodes",schemaPath:"#/properties/nodes/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs8 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.links !== undefined){
let data10 = data.links;
const _errs25 = errors;
if(errors === _errs25){
if(Array.isArray(data10)){
if(data10.length > 300){
validate47.errors = [{instancePath:instancePath+"/links",schemaPath:"#/properties/links/maxItems",keyword:"maxItems",params:{limit: 300},message:"must NOT have more than 300 items"}];
return false;
}
else {
var valid8 = true;
const len2 = data10.length;
for(let i2=0; i2<len2; i2++){
let data11 = data10[i2];
const _errs27 = errors;
if(errors === _errs27){
if(data11 && typeof data11 == "object" && !Array.isArray(data11)){
if(Object.keys(data11).length < 4){
validate47.errors = [{instancePath:instancePath+"/links/" + i2,schemaPath:"#/properties/links/items/minProperties",keyword:"minProperties",params:{limit: 4},message:"must NOT have fewer than 4 properties"}];
return false;
}
else {
const _errs29 = errors;
for(const key2 in data11){
if(!((((key2 === "source") || (key2 === "target")) || (key2 === "value")) || (key2 === "kind"))){
validate47.errors = [{instancePath:instancePath+"/links/" + i2,schemaPath:"#/properties/links/items/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key2},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs29 === errors){
if(data11.source !== undefined){
let data12 = data11.source;
const _errs30 = errors;
const _errs31 = errors;
if(!(((typeof data12 == "number") && (!(data12 % 1) && !isNaN(data12))) && (isFinite(data12)))){
validate47.errors = [{instancePath:instancePath+"/links/" + i2+"/source",schemaPath:"#/$defs/k/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs31){
if((typeof data12 == "number") && (isFinite(data12))){
if(data12 > 499 || isNaN(data12)){
validate47.errors = [{instancePath:instancePath+"/links/" + i2+"/source",schemaPath:"#/$defs/k/maximum",keyword:"maximum",params:{comparison: "<=", limit: 499},message:"must be <= 499"}];
return false;
}
else {
if(data12 < 0 || isNaN(data12)){
validate47.errors = [{instancePath:instancePath+"/links/" + i2+"/source",schemaPath:"#/$defs/k/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid9 = _errs30 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data11.target !== undefined){
let data13 = data11.target;
const _errs33 = errors;
const _errs34 = errors;
if(!(((typeof data13 == "number") && (!(data13 % 1) && !isNaN(data13))) && (isFinite(data13)))){
validate47.errors = [{instancePath:instancePath+"/links/" + i2+"/target",schemaPath:"#/$defs/k/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs34){
if((typeof data13 == "number") && (isFinite(data13))){
if(data13 > 499 || isNaN(data13)){
validate47.errors = [{instancePath:instancePath+"/links/" + i2+"/target",schemaPath:"#/$defs/k/maximum",keyword:"maximum",params:{comparison: "<=", limit: 499},message:"must be <= 499"}];
return false;
}
else {
if(data13 < 0 || isNaN(data13)){
validate47.errors = [{instancePath:instancePath+"/links/" + i2+"/target",schemaPath:"#/$defs/k/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid9 = _errs33 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data11.value !== undefined){
let data14 = data11.value;
const _errs36 = errors;
if(!(((typeof data14 == "number") && (!(data14 % 1) && !isNaN(data14))) && (isFinite(data14)))){
validate47.errors = [{instancePath:instancePath+"/links/" + i2+"/value",schemaPath:"#/properties/links/items/properties/value/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs36){
if((typeof data14 == "number") && (isFinite(data14))){
if(data14 > 1000000 || isNaN(data14)){
validate47.errors = [{instancePath:instancePath+"/links/" + i2+"/value",schemaPath:"#/properties/links/items/properties/value/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000},message:"must be <= 1000000"}];
return false;
}
else {
if(data14 < 1 || isNaN(data14)){
validate47.errors = [{instancePath:instancePath+"/links/" + i2+"/value",schemaPath:"#/properties/links/items/properties/value/minimum",keyword:"minimum",params:{comparison: ">=", limit: 1},message:"must be >= 1"}];
return false;
}
}
}
}
var valid9 = _errs36 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data11.kind !== undefined){
let data15 = data11.kind;
const _errs38 = errors;
if(!((((((data15 === "continuation") || (data15 === "split")) || (data15 === "merge")) || (data15 === "gap")) || (data15 === "newly_observed")) || (data15 === "not_observed"))){
validate47.errors = [{instancePath:instancePath+"/links/" + i2+"/kind",schemaPath:"#/properties/links/items/properties/kind/enum",keyword:"enum",params:{allowedValues: schema103.properties.links.items.properties.kind.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid9 = _errs38 === errors;
}
else {
var valid9 = true;
}
}
}
}
}
}
}
else {
validate47.errors = [{instancePath:instancePath+"/links/" + i2,schemaPath:"#/properties/links/items/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid8 = _errs27 === errors;
if(!valid8){
break;
}
}
}
}
else {
validate47.errors = [{instancePath:instancePath+"/links",schemaPath:"#/properties/links/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs25 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.context !== undefined){
let data16 = data.context;
const _errs39 = errors;
const _errs40 = errors;
if(errors === _errs40){
if(typeof data16 === "string"){
if(func1(data16) > 16384){
validate47.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate47.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs39 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
else {
validate47.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate47.errors = vErrors;
return errors === 0;
}
validate47.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const schema111 = {"type":"object","additionalProperties":false,"minProperties":8,"properties":{"kind":{"const":"inventor-scatter"},"x_label":{"$ref":"#/$defs/c"},"y_label":{"$ref":"#/$defs/c"},"size_label":{"$ref":"#/$defs/c"},"points":{"type":"array","maxItems":40,"items":{"type":"object","additionalProperties":false,"minProperties":6,"properties":{"id":{"$ref":"#/$defs/t"},"label":{"$ref":"#/$defs/t"},"x":{"$ref":"#/$defs/q"},"y":{"$ref":"#/$defs/q"},"size":{"$ref":"#/$defs/u"},"category":{"type":"string","minLength":1,"maxLength":64}}}},"edges":{"type":"array","maxItems":300,"items":{"type":"object","additionalProperties":false,"minProperties":3,"properties":{"source":{"$ref":"#/$defs/k"},"target":{"$ref":"#/$defs/k"},"value":{"$ref":"#/$defs/u"}}}},"unplottable":{"type":"array","maxItems":200,"items":{"type":"object","additionalProperties":false,"minProperties":3,"properties":{"id":{"$ref":"#/$defs/t"},"label":{"$ref":"#/$defs/t"},"reason":{"$ref":"#/$defs/t"}}}},"context":{"$ref":"#/$defs/c"}}};

function validate49(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
let vErrors = null;
let errors = 0;
const evaluated0 = validate49.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
if(Object.keys(data).length < 8){
validate49.errors = [{instancePath,schemaPath:"#/minProperties",keyword:"minProperties",params:{limit: 8},message:"must NOT have fewer than 8 properties"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((((((((key0 === "kind") || (key0 === "x_label")) || (key0 === "y_label")) || (key0 === "size_label")) || (key0 === "points")) || (key0 === "edges")) || (key0 === "unplottable")) || (key0 === "context"))){
validate49.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.kind !== undefined){
const _errs2 = errors;
if("inventor-scatter" !== data.kind){
validate49.errors = [{instancePath:instancePath+"/kind",schemaPath:"#/properties/kind/const",keyword:"const",params:{allowedValue: "inventor-scatter"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.x_label !== undefined){
let data1 = data.x_label;
const _errs3 = errors;
const _errs4 = errors;
if(errors === _errs4){
if(typeof data1 === "string"){
if(func1(data1) > 16384){
validate49.errors = [{instancePath:instancePath+"/x_label",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate49.errors = [{instancePath:instancePath+"/x_label",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.y_label !== undefined){
let data2 = data.y_label;
const _errs6 = errors;
const _errs7 = errors;
if(errors === _errs7){
if(typeof data2 === "string"){
if(func1(data2) > 16384){
validate49.errors = [{instancePath:instancePath+"/y_label",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate49.errors = [{instancePath:instancePath+"/y_label",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs6 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.size_label !== undefined){
let data3 = data.size_label;
const _errs9 = errors;
const _errs10 = errors;
if(errors === _errs10){
if(typeof data3 === "string"){
if(func1(data3) > 16384){
validate49.errors = [{instancePath:instancePath+"/size_label",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate49.errors = [{instancePath:instancePath+"/size_label",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs9 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.points !== undefined){
let data4 = data.points;
const _errs12 = errors;
if(errors === _errs12){
if(Array.isArray(data4)){
if(data4.length > 40){
validate49.errors = [{instancePath:instancePath+"/points",schemaPath:"#/properties/points/maxItems",keyword:"maxItems",params:{limit: 40},message:"must NOT have more than 40 items"}];
return false;
}
else {
var valid4 = true;
const len0 = data4.length;
for(let i0=0; i0<len0; i0++){
let data5 = data4[i0];
const _errs14 = errors;
if(errors === _errs14){
if(data5 && typeof data5 == "object" && !Array.isArray(data5)){
if(Object.keys(data5).length < 6){
validate49.errors = [{instancePath:instancePath+"/points/" + i0,schemaPath:"#/properties/points/items/minProperties",keyword:"minProperties",params:{limit: 6},message:"must NOT have fewer than 6 properties"}];
return false;
}
else {
const _errs16 = errors;
for(const key1 in data5){
if(!((((((key1 === "id") || (key1 === "label")) || (key1 === "x")) || (key1 === "y")) || (key1 === "size")) || (key1 === "category"))){
validate49.errors = [{instancePath:instancePath+"/points/" + i0,schemaPath:"#/properties/points/items/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs16 === errors){
if(data5.id !== undefined){
let data6 = data5.id;
const _errs17 = errors;
const _errs18 = errors;
if(errors === _errs18){
if(typeof data6 === "string"){
if(func1(data6) > 4096){
validate49.errors = [{instancePath:instancePath+"/points/" + i0+"/id",schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data6) < 1){
validate49.errors = [{instancePath:instancePath+"/points/" + i0+"/id",schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate49.errors = [{instancePath:instancePath+"/points/" + i0+"/id",schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid5 = _errs17 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data5.label !== undefined){
let data7 = data5.label;
const _errs20 = errors;
const _errs21 = errors;
if(errors === _errs21){
if(typeof data7 === "string"){
if(func1(data7) > 4096){
validate49.errors = [{instancePath:instancePath+"/points/" + i0+"/label",schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data7) < 1){
validate49.errors = [{instancePath:instancePath+"/points/" + i0+"/label",schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate49.errors = [{instancePath:instancePath+"/points/" + i0+"/label",schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid5 = _errs20 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data5.x !== undefined){
let data8 = data5.x;
const _errs23 = errors;
const _errs24 = errors;
if(errors === _errs24){
if((typeof data8 == "number") && (isFinite(data8))){
if(data8 > 1000000000000 || isNaN(data8)){
validate49.errors = [{instancePath:instancePath+"/points/" + i0+"/x",schemaPath:"#/$defs/q/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000000000},message:"must be <= 1000000000000"}];
return false;
}
else {
if(data8 < -1000000000000 || isNaN(data8)){
validate49.errors = [{instancePath:instancePath+"/points/" + i0+"/x",schemaPath:"#/$defs/q/minimum",keyword:"minimum",params:{comparison: ">=", limit: -1000000000000},message:"must be >= -1000000000000"}];
return false;
}
}
}
else {
validate49.errors = [{instancePath:instancePath+"/points/" + i0+"/x",schemaPath:"#/$defs/q/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid5 = _errs23 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data5.y !== undefined){
let data9 = data5.y;
const _errs26 = errors;
const _errs27 = errors;
if(errors === _errs27){
if((typeof data9 == "number") && (isFinite(data9))){
if(data9 > 1000000000000 || isNaN(data9)){
validate49.errors = [{instancePath:instancePath+"/points/" + i0+"/y",schemaPath:"#/$defs/q/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000000000},message:"must be <= 1000000000000"}];
return false;
}
else {
if(data9 < -1000000000000 || isNaN(data9)){
validate49.errors = [{instancePath:instancePath+"/points/" + i0+"/y",schemaPath:"#/$defs/q/minimum",keyword:"minimum",params:{comparison: ">=", limit: -1000000000000},message:"must be >= -1000000000000"}];
return false;
}
}
}
else {
validate49.errors = [{instancePath:instancePath+"/points/" + i0+"/y",schemaPath:"#/$defs/q/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid5 = _errs26 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data5.size !== undefined){
let data10 = data5.size;
const _errs29 = errors;
const _errs30 = errors;
if(errors === _errs30){
if((typeof data10 == "number") && (isFinite(data10))){
if(data10 > 1000000000000 || isNaN(data10)){
validate49.errors = [{instancePath:instancePath+"/points/" + i0+"/size",schemaPath:"#/$defs/u/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000000000},message:"must be <= 1000000000000"}];
return false;
}
else {
if(data10 < 0 || isNaN(data10)){
validate49.errors = [{instancePath:instancePath+"/points/" + i0+"/size",schemaPath:"#/$defs/u/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
else {
validate49.errors = [{instancePath:instancePath+"/points/" + i0+"/size",schemaPath:"#/$defs/u/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid5 = _errs29 === errors;
}
else {
var valid5 = true;
}
if(valid5){
if(data5.category !== undefined){
let data11 = data5.category;
const _errs32 = errors;
if(errors === _errs32){
if(typeof data11 === "string"){
if(func1(data11) > 64){
validate49.errors = [{instancePath:instancePath+"/points/" + i0+"/category",schemaPath:"#/properties/points/items/properties/category/maxLength",keyword:"maxLength",params:{limit: 64},message:"must NOT have more than 64 characters"}];
return false;
}
else {
if(func1(data11) < 1){
validate49.errors = [{instancePath:instancePath+"/points/" + i0+"/category",schemaPath:"#/properties/points/items/properties/category/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate49.errors = [{instancePath:instancePath+"/points/" + i0+"/category",schemaPath:"#/properties/points/items/properties/category/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid5 = _errs32 === errors;
}
else {
var valid5 = true;
}
}
}
}
}
}
}
}
}
else {
validate49.errors = [{instancePath:instancePath+"/points/" + i0,schemaPath:"#/properties/points/items/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid4 = _errs14 === errors;
if(!valid4){
break;
}
}
}
}
else {
validate49.errors = [{instancePath:instancePath+"/points",schemaPath:"#/properties/points/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs12 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.edges !== undefined){
let data12 = data.edges;
const _errs34 = errors;
if(errors === _errs34){
if(Array.isArray(data12)){
if(data12.length > 300){
validate49.errors = [{instancePath:instancePath+"/edges",schemaPath:"#/properties/edges/maxItems",keyword:"maxItems",params:{limit: 300},message:"must NOT have more than 300 items"}];
return false;
}
else {
var valid11 = true;
const len1 = data12.length;
for(let i1=0; i1<len1; i1++){
let data13 = data12[i1];
const _errs36 = errors;
if(errors === _errs36){
if(data13 && typeof data13 == "object" && !Array.isArray(data13)){
if(Object.keys(data13).length < 3){
validate49.errors = [{instancePath:instancePath+"/edges/" + i1,schemaPath:"#/properties/edges/items/minProperties",keyword:"minProperties",params:{limit: 3},message:"must NOT have fewer than 3 properties"}];
return false;
}
else {
const _errs38 = errors;
for(const key2 in data13){
if(!(((key2 === "source") || (key2 === "target")) || (key2 === "value"))){
validate49.errors = [{instancePath:instancePath+"/edges/" + i1,schemaPath:"#/properties/edges/items/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key2},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs38 === errors){
if(data13.source !== undefined){
let data14 = data13.source;
const _errs39 = errors;
const _errs40 = errors;
if(!(((typeof data14 == "number") && (!(data14 % 1) && !isNaN(data14))) && (isFinite(data14)))){
validate49.errors = [{instancePath:instancePath+"/edges/" + i1+"/source",schemaPath:"#/$defs/k/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs40){
if((typeof data14 == "number") && (isFinite(data14))){
if(data14 > 499 || isNaN(data14)){
validate49.errors = [{instancePath:instancePath+"/edges/" + i1+"/source",schemaPath:"#/$defs/k/maximum",keyword:"maximum",params:{comparison: "<=", limit: 499},message:"must be <= 499"}];
return false;
}
else {
if(data14 < 0 || isNaN(data14)){
validate49.errors = [{instancePath:instancePath+"/edges/" + i1+"/source",schemaPath:"#/$defs/k/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid12 = _errs39 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data13.target !== undefined){
let data15 = data13.target;
const _errs42 = errors;
const _errs43 = errors;
if(!(((typeof data15 == "number") && (!(data15 % 1) && !isNaN(data15))) && (isFinite(data15)))){
validate49.errors = [{instancePath:instancePath+"/edges/" + i1+"/target",schemaPath:"#/$defs/k/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs43){
if((typeof data15 == "number") && (isFinite(data15))){
if(data15 > 499 || isNaN(data15)){
validate49.errors = [{instancePath:instancePath+"/edges/" + i1+"/target",schemaPath:"#/$defs/k/maximum",keyword:"maximum",params:{comparison: "<=", limit: 499},message:"must be <= 499"}];
return false;
}
else {
if(data15 < 0 || isNaN(data15)){
validate49.errors = [{instancePath:instancePath+"/edges/" + i1+"/target",schemaPath:"#/$defs/k/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid12 = _errs42 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data13.value !== undefined){
let data16 = data13.value;
const _errs45 = errors;
const _errs46 = errors;
if(errors === _errs46){
if((typeof data16 == "number") && (isFinite(data16))){
if(data16 > 1000000000000 || isNaN(data16)){
validate49.errors = [{instancePath:instancePath+"/edges/" + i1+"/value",schemaPath:"#/$defs/u/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000000000},message:"must be <= 1000000000000"}];
return false;
}
else {
if(data16 < 0 || isNaN(data16)){
validate49.errors = [{instancePath:instancePath+"/edges/" + i1+"/value",schemaPath:"#/$defs/u/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
else {
validate49.errors = [{instancePath:instancePath+"/edges/" + i1+"/value",schemaPath:"#/$defs/u/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid12 = _errs45 === errors;
}
else {
var valid12 = true;
}
}
}
}
}
}
else {
validate49.errors = [{instancePath:instancePath+"/edges/" + i1,schemaPath:"#/properties/edges/items/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid11 = _errs36 === errors;
if(!valid11){
break;
}
}
}
}
else {
validate49.errors = [{instancePath:instancePath+"/edges",schemaPath:"#/properties/edges/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs34 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.unplottable !== undefined){
let data17 = data.unplottable;
const _errs48 = errors;
if(errors === _errs48){
if(Array.isArray(data17)){
if(data17.length > 200){
validate49.errors = [{instancePath:instancePath+"/unplottable",schemaPath:"#/properties/unplottable/maxItems",keyword:"maxItems",params:{limit: 200},message:"must NOT have more than 200 items"}];
return false;
}
else {
var valid16 = true;
const len2 = data17.length;
for(let i2=0; i2<len2; i2++){
let data18 = data17[i2];
const _errs50 = errors;
if(errors === _errs50){
if(data18 && typeof data18 == "object" && !Array.isArray(data18)){
if(Object.keys(data18).length < 3){
validate49.errors = [{instancePath:instancePath+"/unplottable/" + i2,schemaPath:"#/properties/unplottable/items/minProperties",keyword:"minProperties",params:{limit: 3},message:"must NOT have fewer than 3 properties"}];
return false;
}
else {
const _errs52 = errors;
for(const key3 in data18){
if(!(((key3 === "id") || (key3 === "label")) || (key3 === "reason"))){
validate49.errors = [{instancePath:instancePath+"/unplottable/" + i2,schemaPath:"#/properties/unplottable/items/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key3},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs52 === errors){
if(data18.id !== undefined){
let data19 = data18.id;
const _errs53 = errors;
const _errs54 = errors;
if(errors === _errs54){
if(typeof data19 === "string"){
if(func1(data19) > 4096){
validate49.errors = [{instancePath:instancePath+"/unplottable/" + i2+"/id",schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data19) < 1){
validate49.errors = [{instancePath:instancePath+"/unplottable/" + i2+"/id",schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate49.errors = [{instancePath:instancePath+"/unplottable/" + i2+"/id",schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid17 = _errs53 === errors;
}
else {
var valid17 = true;
}
if(valid17){
if(data18.label !== undefined){
let data20 = data18.label;
const _errs56 = errors;
const _errs57 = errors;
if(errors === _errs57){
if(typeof data20 === "string"){
if(func1(data20) > 4096){
validate49.errors = [{instancePath:instancePath+"/unplottable/" + i2+"/label",schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data20) < 1){
validate49.errors = [{instancePath:instancePath+"/unplottable/" + i2+"/label",schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate49.errors = [{instancePath:instancePath+"/unplottable/" + i2+"/label",schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid17 = _errs56 === errors;
}
else {
var valid17 = true;
}
if(valid17){
if(data18.reason !== undefined){
let data21 = data18.reason;
const _errs59 = errors;
const _errs60 = errors;
if(errors === _errs60){
if(typeof data21 === "string"){
if(func1(data21) > 4096){
validate49.errors = [{instancePath:instancePath+"/unplottable/" + i2+"/reason",schemaPath:"#/$defs/t/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data21) < 1){
validate49.errors = [{instancePath:instancePath+"/unplottable/" + i2+"/reason",schemaPath:"#/$defs/t/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate49.errors = [{instancePath:instancePath+"/unplottable/" + i2+"/reason",schemaPath:"#/$defs/t/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid17 = _errs59 === errors;
}
else {
var valid17 = true;
}
}
}
}
}
}
else {
validate49.errors = [{instancePath:instancePath+"/unplottable/" + i2,schemaPath:"#/properties/unplottable/items/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid16 = _errs50 === errors;
if(!valid16){
break;
}
}
}
}
else {
validate49.errors = [{instancePath:instancePath+"/unplottable",schemaPath:"#/properties/unplottable/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs48 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.context !== undefined){
let data22 = data.context;
const _errs62 = errors;
const _errs63 = errors;
if(errors === _errs63){
if(typeof data22 === "string"){
if(func1(data22) > 16384){
validate49.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/maxLength",keyword:"maxLength",params:{limit: 16384},message:"must NOT have more than 16384 characters"}];
return false;
}
}
else {
validate49.errors = [{instancePath:instancePath+"/context",schemaPath:"#/$defs/c/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs62 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
else {
validate49.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate49.errors = vErrors;
return errors === 0;
}
validate49.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const func84 = Object.prototype.hasOwnProperty;

function validate22(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
/*# sourceURL="urn:patent-analysis:advanced-chart-model:1.0.0" */;
let vErrors = null;
let errors = 0;
const evaluated0 = validate22.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
const _errs1 = errors;
let valid0 = false;
const _errs2 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.analysis_id !== undefined){
const _errs3 = errors;
if("growth-quadrant.v1" !== data.analysis_id){
const err0 = {instancePath:instancePath+"/analysis_id",schemaPath:"#/anyOf/0/properties/analysis_id/const",keyword:"const",params:{allowedValue: "growth-quadrant.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
var valid1 = _errs3 === errors;
}
else {
var valid1 = true;
}
if(valid1){
if(data.mark !== undefined){
const _errs4 = errors;
if("growth-quadrant-svg.v1" !== data.mark){
const err1 = {instancePath:instancePath+"/mark",schemaPath:"#/anyOf/0/properties/mark/const",keyword:"const",params:{allowedValue: "growth-quadrant-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
var valid1 = _errs4 === errors;
}
else {
var valid1 = true;
}
if(valid1){
if(data.title !== undefined){
const _errs5 = errors;
if("長期・短期成長四象限" !== data.title){
const err2 = {instancePath:instancePath+"/title",schemaPath:"#/anyOf/0/properties/title/const",keyword:"const",params:{allowedValue: "長期・短期成長四象限"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
var valid1 = _errs5 === errors;
}
else {
var valid1 = true;
}
if(valid1){
if(data.projection !== undefined){
const _errs6 = errors;
if(!(validate23(data.projection, {instancePath:instancePath+"/projection",parentData:data,parentDataProperty:"projection",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate23.errors : vErrors.concat(validate23.errors);
errors = vErrors.length;
}
var valid1 = _errs6 === errors;
}
else {
var valid1 = true;
}
}
}
}
}
var _valid0 = _errs2 === errors;
valid0 = valid0 || _valid0;
if(_valid0){
var props0 = {};
props0.analysis_id = true;
props0.mark = true;
props0.title = true;
props0.projection = true;
}
const _errs7 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.analysis_id !== undefined){
const _errs8 = errors;
if("entry-exit.v1" !== data.analysis_id){
const err3 = {instancePath:instancePath+"/analysis_id",schemaPath:"#/anyOf/1/properties/analysis_id/const",keyword:"const",params:{allowedValue: "entry-exit.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
var valid2 = _errs8 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data.mark !== undefined){
const _errs9 = errors;
if("entry-exit-svg.v1" !== data.mark){
const err4 = {instancePath:instancePath+"/mark",schemaPath:"#/anyOf/1/properties/mark/const",keyword:"const",params:{allowedValue: "entry-exit-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
var valid2 = _errs9 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data.title !== undefined){
const _errs10 = errors;
if("初回・最終観測年" !== data.title){
const err5 = {instancePath:instancePath+"/title",schemaPath:"#/anyOf/1/properties/title/const",keyword:"const",params:{allowedValue: "初回・最終観測年"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
var valid2 = _errs10 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data.projection !== undefined){
let data7 = data.projection;
const _errs11 = errors;
if(!(validate25(data7, {instancePath:instancePath+"/projection",parentData:data,parentDataProperty:"projection",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate25.errors : vErrors.concat(validate25.errors);
errors = vErrors.length;
}
if(errors === _errs11){
if(data7 && typeof data7 == "object" && !Array.isArray(data7)){
if(data7.x_year !== undefined){
const _errs13 = errors;
if(true !== data7.x_year){
const err6 = {instancePath:instancePath+"/projection/x_year",schemaPath:"#/anyOf/1/properties/projection/properties/x_year/const",keyword:"const",params:{allowedValue: true},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
}
var valid3 = _errs13 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data7.y_year !== undefined){
const _errs14 = errors;
if(true !== data7.y_year){
const err7 = {instancePath:instancePath+"/projection/y_year",schemaPath:"#/anyOf/1/properties/projection/properties/y_year/const",keyword:"const",params:{allowedValue: true},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
var valid3 = _errs14 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data7.x_label !== undefined){
const _errs15 = errors;
if("初回観測年" !== data7.x_label){
const err8 = {instancePath:instancePath+"/projection/x_label",schemaPath:"#/anyOf/1/properties/projection/properties/x_label/const",keyword:"const",params:{allowedValue: "初回観測年"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
}
var valid3 = _errs15 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data7.y_label !== undefined){
const _errs16 = errors;
if("最終観測年" !== data7.y_label){
const err9 = {instancePath:instancePath+"/projection/y_label",schemaPath:"#/anyOf/1/properties/projection/properties/y_label/const",keyword:"const",params:{allowedValue: "最終観測年"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
}
var valid3 = _errs16 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data7.size_label !== undefined){
const _errs17 = errors;
if("件数" !== data7.size_label){
const err10 = {instancePath:instancePath+"/projection/size_label",schemaPath:"#/anyOf/1/properties/projection/properties/size_label/const",keyword:"const",params:{allowedValue: "件数"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err10];
}
else {
vErrors.push(err10);
}
errors++;
}
var valid3 = _errs17 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data7.points !== undefined){
let data13 = data7.points;
const _errs18 = errors;
if(errors === _errs18){
if(Array.isArray(data13)){
var valid4 = true;
const len0 = data13.length;
for(let i0=0; i0<len0; i0++){
let data14 = data13[i0];
const _errs20 = errors;
if(errors === _errs20){
if(data14 && typeof data14 == "object" && !Array.isArray(data14)){
if(data14.category !== undefined){
let data15 = data14.category;
if(!((data15 === "active") || (data15 === "inactive"))){
const err11 = {instancePath:instancePath+"/projection/points/" + i0+"/category",schemaPath:"#/anyOf/1/properties/projection/properties/points/items/properties/category/enum",keyword:"enum",params:{allowedValues: schema33.anyOf[1].properties.projection.properties.points.items.properties.category.enum},message:"must be equal to one of the allowed values"};
if(vErrors === null){
vErrors = [err11];
}
else {
vErrors.push(err11);
}
errors++;
}
}
}
else {
const err12 = {instancePath:instancePath+"/projection/points/" + i0,schemaPath:"#/anyOf/1/properties/projection/properties/points/items/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err12];
}
else {
vErrors.push(err12);
}
errors++;
}
}
var valid4 = _errs20 === errors;
if(!valid4){
break;
}
}
}
else {
const err13 = {instancePath:instancePath+"/projection/points",schemaPath:"#/anyOf/1/properties/projection/properties/points/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err13];
}
else {
vErrors.push(err13);
}
errors++;
}
}
var valid3 = _errs18 === errors;
}
else {
var valid3 = true;
}
}
}
}
}
}
}
else {
const err14 = {instancePath:instancePath+"/projection",schemaPath:"#/anyOf/1/properties/projection/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err14];
}
else {
vErrors.push(err14);
}
errors++;
}
}
var valid2 = _errs11 === errors;
}
else {
var valid2 = true;
}
}
}
}
}
var _valid0 = _errs7 === errors;
valid0 = valid0 || _valid0;
if(_valid0){
if(props0 !== true){
props0 = props0 || {};
props0.analysis_id = true;
props0.mark = true;
props0.title = true;
props0.projection = true;
}
}
const _errs23 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.analysis_id !== undefined){
const _errs24 = errors;
if("citation.v1" !== data.analysis_id){
const err15 = {instancePath:instancePath+"/analysis_id",schemaPath:"#/anyOf/2/properties/analysis_id/const",keyword:"const",params:{allowedValue: "citation.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err15];
}
else {
vErrors.push(err15);
}
errors++;
}
var valid6 = _errs24 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data.mark !== undefined){
const _errs25 = errors;
if("citation-svg.v1" !== data.mark){
const err16 = {instancePath:instancePath+"/mark",schemaPath:"#/anyOf/2/properties/mark/const",keyword:"const",params:{allowedValue: "citation-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err16];
}
else {
vErrors.push(err16);
}
errors++;
}
var valid6 = _errs25 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data.title !== undefined){
const _errs26 = errors;
if("レコード別被引用マップ" !== data.title){
const err17 = {instancePath:instancePath+"/title",schemaPath:"#/anyOf/2/properties/title/const",keyword:"const",params:{allowedValue: "レコード別被引用マップ"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err17];
}
else {
vErrors.push(err17);
}
errors++;
}
var valid6 = _errs26 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data.projection !== undefined){
let data19 = data.projection;
const _errs27 = errors;
if(!(validate25(data19, {instancePath:instancePath+"/projection",parentData:data,parentDataProperty:"projection",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate25.errors : vErrors.concat(validate25.errors);
errors = vErrors.length;
}
if(errors === _errs27){
if(data19 && typeof data19 == "object" && !Array.isArray(data19)){
if(data19.x_year !== undefined){
const _errs29 = errors;
if(true !== data19.x_year){
const err18 = {instancePath:instancePath+"/projection/x_year",schemaPath:"#/anyOf/2/properties/projection/properties/x_year/const",keyword:"const",params:{allowedValue: true},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err18];
}
else {
vErrors.push(err18);
}
errors++;
}
var valid7 = _errs29 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data19.y_year !== undefined){
const _errs30 = errors;
if(false !== data19.y_year){
const err19 = {instancePath:instancePath+"/projection/y_year",schemaPath:"#/anyOf/2/properties/projection/properties/y_year/const",keyword:"const",params:{allowedValue: false},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err19];
}
else {
vErrors.push(err19);
}
errors++;
}
var valid7 = _errs30 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data19.x_label !== undefined){
const _errs31 = errors;
if("観測年" !== data19.x_label){
const err20 = {instancePath:instancePath+"/projection/x_label",schemaPath:"#/anyOf/2/properties/projection/properties/x_label/const",keyword:"const",params:{allowedValue: "観測年"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err20];
}
else {
vErrors.push(err20);
}
errors++;
}
var valid7 = _errs31 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data19.y_label !== undefined){
const _errs32 = errors;
if("被引用件数" !== data19.y_label){
const err21 = {instancePath:instancePath+"/projection/y_label",schemaPath:"#/anyOf/2/properties/projection/properties/y_label/const",keyword:"const",params:{allowedValue: "被引用件数"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err21];
}
else {
vErrors.push(err21);
}
errors++;
}
var valid7 = _errs32 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data19.size_label !== undefined){
const _errs33 = errors;
if("被引用件数" !== data19.size_label){
const err22 = {instancePath:instancePath+"/projection/size_label",schemaPath:"#/anyOf/2/properties/projection/properties/size_label/const",keyword:"const",params:{allowedValue: "被引用件数"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err22];
}
else {
vErrors.push(err22);
}
errors++;
}
var valid7 = _errs33 === errors;
}
else {
var valid7 = true;
}
if(valid7){
if(data19.points !== undefined){
let data25 = data19.points;
const _errs34 = errors;
if(errors === _errs34){
if(Array.isArray(data25)){
var valid8 = true;
const len1 = data25.length;
for(let i1=0; i1<len1; i1++){
let data26 = data25[i1];
const _errs36 = errors;
if(errors === _errs36){
if(data26 && typeof data26 == "object" && !Array.isArray(data26)){
if(data26.category !== undefined){
if(!(data26.category === "citation")){
const err23 = {instancePath:instancePath+"/projection/points/" + i1+"/category",schemaPath:"#/anyOf/2/properties/projection/properties/points/items/properties/category/enum",keyword:"enum",params:{allowedValues: schema33.anyOf[2].properties.projection.properties.points.items.properties.category.enum},message:"must be equal to one of the allowed values"};
if(vErrors === null){
vErrors = [err23];
}
else {
vErrors.push(err23);
}
errors++;
}
}
}
else {
const err24 = {instancePath:instancePath+"/projection/points/" + i1,schemaPath:"#/anyOf/2/properties/projection/properties/points/items/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err24];
}
else {
vErrors.push(err24);
}
errors++;
}
}
var valid8 = _errs36 === errors;
if(!valid8){
break;
}
}
}
else {
const err25 = {instancePath:instancePath+"/projection/points",schemaPath:"#/anyOf/2/properties/projection/properties/points/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err25];
}
else {
vErrors.push(err25);
}
errors++;
}
}
var valid7 = _errs34 === errors;
}
else {
var valid7 = true;
}
}
}
}
}
}
}
else {
const err26 = {instancePath:instancePath+"/projection",schemaPath:"#/anyOf/2/properties/projection/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err26];
}
else {
vErrors.push(err26);
}
errors++;
}
}
var valid6 = _errs27 === errors;
}
else {
var valid6 = true;
}
}
}
}
}
var _valid0 = _errs23 === errors;
valid0 = valid0 || _valid0;
if(_valid0){
if(props0 !== true){
props0 = props0 || {};
props0.analysis_id = true;
props0.mark = true;
props0.title = true;
props0.projection = true;
}
}
const _errs39 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.analysis_id !== undefined){
const _errs40 = errors;
if("matrix-composition.v1" !== data.analysis_id){
const err27 = {instancePath:instancePath+"/analysis_id",schemaPath:"#/anyOf/3/properties/analysis_id/const",keyword:"const",params:{allowedValue: "matrix-composition.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err27];
}
else {
vErrors.push(err27);
}
errors++;
}
var valid10 = _errs40 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data.mark !== undefined){
const _errs41 = errors;
if("matrix-composition-svg.v1" !== data.mark){
const err28 = {instancePath:instancePath+"/mark",schemaPath:"#/anyOf/3/properties/mark/const",keyword:"const",params:{allowedValue: "matrix-composition-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err28];
}
else {
vErrors.push(err28);
}
errors++;
}
var valid10 = _errs41 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data.title !== undefined){
const _errs42 = errors;
if("選択セルの構成内訳" !== data.title){
const err29 = {instancePath:instancePath+"/title",schemaPath:"#/anyOf/3/properties/title/const",keyword:"const",params:{allowedValue: "選択セルの構成内訳"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err29];
}
else {
vErrors.push(err29);
}
errors++;
}
var valid10 = _errs42 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data.projection !== undefined){
const _errs43 = errors;
if(!(validate28(data.projection, {instancePath:instancePath+"/projection",parentData:data,parentDataProperty:"projection",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate28.errors : vErrors.concat(validate28.errors);
errors = vErrors.length;
}
var valid10 = _errs43 === errors;
}
else {
var valid10 = true;
}
}
}
}
}
var _valid0 = _errs39 === errors;
valid0 = valid0 || _valid0;
if(_valid0){
if(props0 !== true){
props0 = props0 || {};
props0.analysis_id = true;
props0.mark = true;
props0.title = true;
props0.projection = true;
}
}
const _errs44 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.analysis_id !== undefined){
const _errs45 = errors;
if("new-entrants.v1" !== data.analysis_id){
const err30 = {instancePath:instancePath+"/analysis_id",schemaPath:"#/anyOf/4/properties/analysis_id/const",keyword:"const",params:{allowedValue: "new-entrants.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err30];
}
else {
vErrors.push(err30);
}
errors++;
}
var valid11 = _errs45 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data.mark !== undefined){
const _errs46 = errors;
if("new-entrants-svg.v1" !== data.mark){
const err31 = {instancePath:instancePath+"/mark",schemaPath:"#/anyOf/4/properties/mark/const",keyword:"const",params:{allowedValue: "new-entrants-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err31];
}
else {
vErrors.push(err31);
}
errors++;
}
var valid11 = _errs46 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data.title !== undefined){
const _errs47 = errors;
if("母集団内の新規参入者と分類" !== data.title){
const err32 = {instancePath:instancePath+"/title",schemaPath:"#/anyOf/4/properties/title/const",keyword:"const",params:{allowedValue: "母集団内の新規参入者と分類"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err32];
}
else {
vErrors.push(err32);
}
errors++;
}
var valid11 = _errs47 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data.projection !== undefined){
const _errs48 = errors;
if(!(validate30(data.projection, {instancePath:instancePath+"/projection",parentData:data,parentDataProperty:"projection",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate30.errors : vErrors.concat(validate30.errors);
errors = vErrors.length;
}
var valid11 = _errs48 === errors;
}
else {
var valid11 = true;
}
}
}
}
}
var _valid0 = _errs44 === errors;
valid0 = valid0 || _valid0;
if(_valid0){
if(props0 !== true){
props0 = props0 || {};
props0.analysis_id = true;
props0.mark = true;
props0.title = true;
props0.projection = true;
}
}
const _errs49 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.analysis_id !== undefined){
const _errs50 = errors;
if("compara.v1" !== data.analysis_id){
const err33 = {instancePath:instancePath+"/analysis_id",schemaPath:"#/anyOf/5/properties/analysis_id/const",keyword:"const",params:{allowedValue: "compara.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err33];
}
else {
vErrors.push(err33);
}
errors++;
}
var valid12 = _errs50 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data.mark !== undefined){
const _errs51 = errors;
if("compara-svg.v1" !== data.mark){
const err34 = {instancePath:instancePath+"/mark",schemaPath:"#/anyOf/5/properties/mark/const",keyword:"const",params:{allowedValue: "compara-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err34];
}
else {
vErrors.push(err34);
}
errors++;
}
var valid12 = _errs51 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data.title !== undefined){
const _errs52 = errors;
if("グループ間の件数差分" !== data.title){
const err35 = {instancePath:instancePath+"/title",schemaPath:"#/anyOf/5/properties/title/const",keyword:"const",params:{allowedValue: "グループ間の件数差分"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err35];
}
else {
vErrors.push(err35);
}
errors++;
}
var valid12 = _errs52 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data.projection !== undefined){
const _errs53 = errors;
if(!(validate30(data.projection, {instancePath:instancePath+"/projection",parentData:data,parentDataProperty:"projection",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate30.errors : vErrors.concat(validate30.errors);
errors = vErrors.length;
}
var valid12 = _errs53 === errors;
}
else {
var valid12 = true;
}
}
}
}
}
var _valid0 = _errs49 === errors;
valid0 = valid0 || _valid0;
if(_valid0){
if(props0 !== true){
props0 = props0 || {};
props0.analysis_id = true;
props0.mark = true;
props0.title = true;
props0.projection = true;
}
}
const _errs54 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.analysis_id !== undefined){
const _errs55 = errors;
if("cooccurrence.v1" !== data.analysis_id){
const err36 = {instancePath:instancePath+"/analysis_id",schemaPath:"#/anyOf/6/properties/analysis_id/const",keyword:"const",params:{allowedValue: "cooccurrence.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err36];
}
else {
vErrors.push(err36);
}
errors++;
}
var valid13 = _errs55 === errors;
}
else {
var valid13 = true;
}
if(valid13){
if(data.mark !== undefined){
const _errs56 = errors;
if("cooccurrence-svg.v1" !== data.mark){
const err37 = {instancePath:instancePath+"/mark",schemaPath:"#/anyOf/6/properties/mark/const",keyword:"const",params:{allowedValue: "cooccurrence-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err37];
}
else {
vErrors.push(err37);
}
errors++;
}
var valid13 = _errs56 === errors;
}
else {
var valid13 = true;
}
if(valid13){
if(data.title !== undefined){
const _errs57 = errors;
if("分類の共起件数" !== data.title){
const err38 = {instancePath:instancePath+"/title",schemaPath:"#/anyOf/6/properties/title/const",keyword:"const",params:{allowedValue: "分類の共起件数"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err38];
}
else {
vErrors.push(err38);
}
errors++;
}
var valid13 = _errs57 === errors;
}
else {
var valid13 = true;
}
if(valid13){
if(data.projection !== undefined){
const _errs58 = errors;
if(!(validate30(data.projection, {instancePath:instancePath+"/projection",parentData:data,parentDataProperty:"projection",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate30.errors : vErrors.concat(validate30.errors);
errors = vErrors.length;
}
var valid13 = _errs58 === errors;
}
else {
var valid13 = true;
}
}
}
}
}
var _valid0 = _errs54 === errors;
valid0 = valid0 || _valid0;
if(_valid0){
if(props0 !== true){
props0 = props0 || {};
props0.analysis_id = true;
props0.mark = true;
props0.title = true;
props0.projection = true;
}
}
const _errs59 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.analysis_id !== undefined){
const _errs60 = errors;
if("collaboration-network.v1" !== data.analysis_id){
const err39 = {instancePath:instancePath+"/analysis_id",schemaPath:"#/anyOf/7/properties/analysis_id/const",keyword:"const",params:{allowedValue: "collaboration-network.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err39];
}
else {
vErrors.push(err39);
}
errors++;
}
var valid14 = _errs60 === errors;
}
else {
var valid14 = true;
}
if(valid14){
if(data.mark !== undefined){
const _errs61 = errors;
if("collaboration-network-svg.v1" !== data.mark){
const err40 = {instancePath:instancePath+"/mark",schemaPath:"#/anyOf/7/properties/mark/const",keyword:"const",params:{allowedValue: "collaboration-network-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err40];
}
else {
vErrors.push(err40);
}
errors++;
}
var valid14 = _errs61 === errors;
}
else {
var valid14 = true;
}
if(valid14){
if(data.title !== undefined){
const _errs62 = errors;
if("共同関係ネットワーク" !== data.title){
const err41 = {instancePath:instancePath+"/title",schemaPath:"#/anyOf/7/properties/title/const",keyword:"const",params:{allowedValue: "共同関係ネットワーク"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err41];
}
else {
vErrors.push(err41);
}
errors++;
}
var valid14 = _errs62 === errors;
}
else {
var valid14 = true;
}
if(valid14){
if(data.projection !== undefined){
const _errs63 = errors;
if(!(validate34(data.projection, {instancePath:instancePath+"/projection",parentData:data,parentDataProperty:"projection",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate34.errors : vErrors.concat(validate34.errors);
errors = vErrors.length;
}
var valid14 = _errs63 === errors;
}
else {
var valid14 = true;
}
}
}
}
}
var _valid0 = _errs59 === errors;
valid0 = valid0 || _valid0;
if(_valid0){
if(props0 !== true){
props0 = props0 || {};
props0.analysis_id = true;
props0.mark = true;
props0.title = true;
props0.projection = true;
}
}
const _errs64 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.analysis_id !== undefined){
const _errs65 = errors;
if("uniqueness.v1" !== data.analysis_id){
const err42 = {instancePath:instancePath+"/analysis_id",schemaPath:"#/anyOf/8/properties/analysis_id/const",keyword:"const",params:{allowedValue: "uniqueness.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err42];
}
else {
vErrors.push(err42);
}
errors++;
}
var valid15 = _errs65 === errors;
}
else {
var valid15 = true;
}
if(valid15){
if(data.mark !== undefined){
const _errs66 = errors;
if("uniqueness-svg.v1" !== data.mark){
const err43 = {instancePath:instancePath+"/mark",schemaPath:"#/anyOf/8/properties/mark/const",keyword:"const",params:{allowedValue: "uniqueness-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err43];
}
else {
vErrors.push(err43);
}
errors++;
}
var valid15 = _errs66 === errors;
}
else {
var valid15 = true;
}
if(valid15){
if(data.title !== undefined){
const _errs67 = errors;
if("グループ別の固有項目" !== data.title){
const err44 = {instancePath:instancePath+"/title",schemaPath:"#/anyOf/8/properties/title/const",keyword:"const",params:{allowedValue: "グループ別の固有項目"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err44];
}
else {
vErrors.push(err44);
}
errors++;
}
var valid15 = _errs67 === errors;
}
else {
var valid15 = true;
}
if(valid15){
if(data.projection !== undefined){
const _errs68 = errors;
if(!(validate28(data.projection, {instancePath:instancePath+"/projection",parentData:data,parentDataProperty:"projection",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate28.errors : vErrors.concat(validate28.errors);
errors = vErrors.length;
}
var valid15 = _errs68 === errors;
}
else {
var valid15 = true;
}
}
}
}
}
var _valid0 = _errs64 === errors;
valid0 = valid0 || _valid0;
if(_valid0){
if(props0 !== true){
props0 = props0 || {};
props0.analysis_id = true;
props0.mark = true;
props0.title = true;
props0.projection = true;
}
}
const _errs69 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.analysis_id !== undefined){
const _errs70 = errors;
if("shared-involvement.v1" !== data.analysis_id){
const err45 = {instancePath:instancePath+"/analysis_id",schemaPath:"#/anyOf/9/properties/analysis_id/const",keyword:"const",params:{allowedValue: "shared-involvement.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err45];
}
else {
vErrors.push(err45);
}
errors++;
}
var valid16 = _errs70 === errors;
}
else {
var valid16 = true;
}
if(valid16){
if(data.mark !== undefined){
const _errs71 = errors;
if("shared-involvement-svg.v1" !== data.mark){
const err46 = {instancePath:instancePath+"/mark",schemaPath:"#/anyOf/9/properties/mark/const",keyword:"const",params:{allowedValue: "shared-involvement-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err46];
}
else {
vErrors.push(err46);
}
errors++;
}
var valid16 = _errs71 === errors;
}
else {
var valid16 = true;
}
if(valid16){
if(data.title !== undefined){
const _errs72 = errors;
if("グループ別の共有項目と関与" !== data.title){
const err47 = {instancePath:instancePath+"/title",schemaPath:"#/anyOf/9/properties/title/const",keyword:"const",params:{allowedValue: "グループ別の共有項目と関与"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err47];
}
else {
vErrors.push(err47);
}
errors++;
}
var valid16 = _errs72 === errors;
}
else {
var valid16 = true;
}
if(valid16){
if(data.projection !== undefined){
const _errs73 = errors;
if(!(validate28(data.projection, {instancePath:instancePath+"/projection",parentData:data,parentDataProperty:"projection",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate28.errors : vErrors.concat(validate28.errors);
errors = vErrors.length;
}
var valid16 = _errs73 === errors;
}
else {
var valid16 = true;
}
}
}
}
}
var _valid0 = _errs69 === errors;
valid0 = valid0 || _valid0;
if(_valid0){
if(props0 !== true){
props0 = props0 || {};
props0.analysis_id = true;
props0.mark = true;
props0.title = true;
props0.projection = true;
}
}
const _errs74 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.analysis_id !== undefined){
const _errs75 = errors;
if("inventor-tracking.v1" !== data.analysis_id){
const err48 = {instancePath:instancePath+"/analysis_id",schemaPath:"#/anyOf/10/properties/analysis_id/const",keyword:"const",params:{allowedValue: "inventor-tracking.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err48];
}
else {
vErrors.push(err48);
}
errors++;
}
var valid17 = _errs75 === errors;
}
else {
var valid17 = true;
}
if(valid17){
if(data.mark !== undefined){
const _errs76 = errors;
if("inventor-tracking-svg.v1" !== data.mark){
const err49 = {instancePath:instancePath+"/mark",schemaPath:"#/anyOf/10/properties/mark/const",keyword:"const",params:{allowedValue: "inventor-tracking-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err49];
}
else {
vErrors.push(err49);
}
errors++;
}
var valid17 = _errs76 === errors;
}
else {
var valid17 = true;
}
if(valid17){
if(data.title !== undefined){
const _errs77 = errors;
if("発明者・共発明クラスタの年次追跡" !== data.title){
const err50 = {instancePath:instancePath+"/title",schemaPath:"#/anyOf/10/properties/title/const",keyword:"const",params:{allowedValue: "発明者・共発明クラスタの年次追跡"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err50];
}
else {
vErrors.push(err50);
}
errors++;
}
var valid17 = _errs77 === errors;
}
else {
var valid17 = true;
}
if(valid17){
if(data.projection !== undefined){
const _errs78 = errors;
if(!(validate38(data.projection, {instancePath:instancePath+"/projection",parentData:data,parentDataProperty:"projection",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate38.errors : vErrors.concat(validate38.errors);
errors = vErrors.length;
}
var valid17 = _errs78 === errors;
}
else {
var valid17 = true;
}
}
}
}
}
var _valid0 = _errs74 === errors;
valid0 = valid0 || _valid0;
if(_valid0){
if(props0 !== true){
props0 = props0 || {};
props0.analysis_id = true;
props0.mark = true;
props0.title = true;
props0.projection = true;
}
}
const _errs79 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.analysis_id !== undefined){
const _errs80 = errors;
if("inventor-network.v1" !== data.analysis_id){
const err51 = {instancePath:instancePath+"/analysis_id",schemaPath:"#/anyOf/11/properties/analysis_id/const",keyword:"const",params:{allowedValue: "inventor-network.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err51];
}
else {
vErrors.push(err51);
}
errors++;
}
var valid18 = _errs80 === errors;
}
else {
var valid18 = true;
}
if(valid18){
if(data.mark !== undefined){
const _errs81 = errors;
if("inventor-network-svg.v1" !== data.mark){
const err52 = {instancePath:instancePath+"/mark",schemaPath:"#/anyOf/11/properties/mark/const",keyword:"const",params:{allowedValue: "inventor-network-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err52];
}
else {
vErrors.push(err52);
}
errors++;
}
var valid18 = _errs81 === errors;
}
else {
var valid18 = true;
}
if(valid18){
if(data.title !== undefined){
const _errs82 = errors;
if("共発明ネットワーク" !== data.title){
const err53 = {instancePath:instancePath+"/title",schemaPath:"#/anyOf/11/properties/title/const",keyword:"const",params:{allowedValue: "共発明ネットワーク"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err53];
}
else {
vErrors.push(err53);
}
errors++;
}
var valid18 = _errs82 === errors;
}
else {
var valid18 = true;
}
if(valid18){
if(data.projection !== undefined){
const _errs83 = errors;
if(!(validate40(data.projection, {instancePath:instancePath+"/projection",parentData:data,parentDataProperty:"projection",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate40.errors : vErrors.concat(validate40.errors);
errors = vErrors.length;
}
var valid18 = _errs83 === errors;
}
else {
var valid18 = true;
}
}
}
}
}
var _valid0 = _errs79 === errors;
valid0 = valid0 || _valid0;
if(_valid0){
if(props0 !== true){
props0 = props0 || {};
props0.analysis_id = true;
props0.mark = true;
props0.title = true;
props0.projection = true;
}
}
const _errs84 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.analysis_id !== undefined){
const _errs85 = errors;
if("inventor-ego-network.v1" !== data.analysis_id){
const err54 = {instancePath:instancePath+"/analysis_id",schemaPath:"#/anyOf/12/properties/analysis_id/const",keyword:"const",params:{allowedValue: "inventor-ego-network.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err54];
}
else {
vErrors.push(err54);
}
errors++;
}
var valid19 = _errs85 === errors;
}
else {
var valid19 = true;
}
if(valid19){
if(data.mark !== undefined){
const _errs86 = errors;
if("inventor-ego-network-svg.v1" !== data.mark){
const err55 = {instancePath:instancePath+"/mark",schemaPath:"#/anyOf/12/properties/mark/const",keyword:"const",params:{allowedValue: "inventor-ego-network-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err55];
}
else {
vErrors.push(err55);
}
errors++;
}
var valid19 = _errs86 === errors;
}
else {
var valid19 = true;
}
if(valid19){
if(data.title !== undefined){
const _errs87 = errors;
if("発明者中心の関係マップ" !== data.title){
const err56 = {instancePath:instancePath+"/title",schemaPath:"#/anyOf/12/properties/title/const",keyword:"const",params:{allowedValue: "発明者中心の関係マップ"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err56];
}
else {
vErrors.push(err56);
}
errors++;
}
var valid19 = _errs87 === errors;
}
else {
var valid19 = true;
}
if(valid19){
if(data.projection !== undefined){
let data67 = data.projection;
const _errs88 = errors;
if(!(validate40(data67, {instancePath:instancePath+"/projection",parentData:data,parentDataProperty:"projection",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate40.errors : vErrors.concat(validate40.errors);
errors = vErrors.length;
}
if(errors === _errs88){
if(data67 && typeof data67 == "object" && !Array.isArray(data67)){
if(data67.focus !== undefined){
if(typeof data67.focus !== "string"){
const err57 = {instancePath:instancePath+"/projection/focus",schemaPath:"#/anyOf/12/properties/projection/properties/focus/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err57];
}
else {
vErrors.push(err57);
}
errors++;
}
}
}
else {
const err58 = {instancePath:instancePath+"/projection",schemaPath:"#/anyOf/12/properties/projection/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err58];
}
else {
vErrors.push(err58);
}
errors++;
}
}
var valid19 = _errs88 === errors;
}
else {
var valid19 = true;
}
}
}
}
}
var _valid0 = _errs84 === errors;
valid0 = valid0 || _valid0;
if(_valid0){
if(props0 !== true){
props0 = props0 || {};
props0.analysis_id = true;
props0.mark = true;
props0.title = true;
props0.projection = true;
}
}
const _errs92 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.analysis_id !== undefined){
const _errs93 = errors;
if("inventor-technology.v1" !== data.analysis_id){
const err59 = {instancePath:instancePath+"/analysis_id",schemaPath:"#/anyOf/13/properties/analysis_id/const",keyword:"const",params:{allowedValue: "inventor-technology.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err59];
}
else {
vErrors.push(err59);
}
errors++;
}
var valid21 = _errs93 === errors;
}
else {
var valid21 = true;
}
if(valid21){
if(data.mark !== undefined){
const _errs94 = errors;
if("inventor-technology-svg.v1" !== data.mark){
const err60 = {instancePath:instancePath+"/mark",schemaPath:"#/anyOf/13/properties/mark/const",keyword:"const",params:{allowedValue: "inventor-technology-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err60];
}
else {
vErrors.push(err60);
}
errors++;
}
var valid21 = _errs94 === errors;
}
else {
var valid21 = true;
}
if(valid21){
if(data.title !== undefined){
const _errs95 = errors;
if("発明者×技術分野" !== data.title){
const err61 = {instancePath:instancePath+"/title",schemaPath:"#/anyOf/13/properties/title/const",keyword:"const",params:{allowedValue: "発明者×技術分野"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err61];
}
else {
vErrors.push(err61);
}
errors++;
}
var valid21 = _errs95 === errors;
}
else {
var valid21 = true;
}
if(valid21){
if(data.projection !== undefined){
const _errs96 = errors;
if(!(validate43(data.projection, {instancePath:instancePath+"/projection",parentData:data,parentDataProperty:"projection",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate43.errors : vErrors.concat(validate43.errors);
errors = vErrors.length;
}
var valid21 = _errs96 === errors;
}
else {
var valid21 = true;
}
}
}
}
}
var _valid0 = _errs92 === errors;
valid0 = valid0 || _valid0;
if(_valid0){
if(props0 !== true){
props0 = props0 || {};
props0.analysis_id = true;
props0.mark = true;
props0.title = true;
props0.projection = true;
}
}
const _errs97 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.analysis_id !== undefined){
const _errs98 = errors;
if("inventor-activity.v1" !== data.analysis_id){
const err62 = {instancePath:instancePath+"/analysis_id",schemaPath:"#/anyOf/14/properties/analysis_id/const",keyword:"const",params:{allowedValue: "inventor-activity.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err62];
}
else {
vErrors.push(err62);
}
errors++;
}
var valid22 = _errs98 === errors;
}
else {
var valid22 = true;
}
if(valid22){
if(data.mark !== undefined){
const _errs99 = errors;
if("inventor-activity-svg.v1" !== data.mark){
const err63 = {instancePath:instancePath+"/mark",schemaPath:"#/anyOf/14/properties/mark/const",keyword:"const",params:{allowedValue: "inventor-activity-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err63];
}
else {
vErrors.push(err63);
}
errors++;
}
var valid22 = _errs99 === errors;
}
else {
var valid22 = true;
}
if(valid22){
if(data.title !== undefined){
const _errs100 = errors;
if("発明者の活動履歴" !== data.title){
const err64 = {instancePath:instancePath+"/title",schemaPath:"#/anyOf/14/properties/title/const",keyword:"const",params:{allowedValue: "発明者の活動履歴"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err64];
}
else {
vErrors.push(err64);
}
errors++;
}
var valid22 = _errs100 === errors;
}
else {
var valid22 = true;
}
if(valid22){
if(data.projection !== undefined){
let data76 = data.projection;
const _errs101 = errors;
if(!(validate45(data76, {instancePath:instancePath+"/projection",parentData:data,parentDataProperty:"projection",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate45.errors : vErrors.concat(validate45.errors);
errors = vErrors.length;
}
if(errors === _errs101){
if(data76 && typeof data76 == "object" && !Array.isArray(data76)){
if(data76.bands !== undefined){
let data77 = data76.bands;
const _errs103 = errors;
if(errors === _errs103){
if(Array.isArray(data77)){
if(data77.length > 0){
const err65 = {instancePath:instancePath+"/projection/bands",schemaPath:"#/anyOf/14/properties/projection/properties/bands/maxItems",keyword:"maxItems",params:{limit: 0},message:"must NOT have more than 0 items"};
if(vErrors === null){
vErrors = [err65];
}
else {
vErrors.push(err65);
}
errors++;
}
}
else {
const err66 = {instancePath:instancePath+"/projection/bands",schemaPath:"#/anyOf/14/properties/projection/properties/bands/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err66];
}
else {
vErrors.push(err66);
}
errors++;
}
}
}
}
else {
const err67 = {instancePath:instancePath+"/projection",schemaPath:"#/anyOf/14/properties/projection/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err67];
}
else {
vErrors.push(err67);
}
errors++;
}
}
var valid22 = _errs101 === errors;
}
else {
var valid22 = true;
}
}
}
}
}
var _valid0 = _errs97 === errors;
valid0 = valid0 || _valid0;
if(_valid0){
if(props0 !== true){
props0 = props0 || {};
props0.analysis_id = true;
props0.mark = true;
props0.title = true;
props0.projection = true;
}
}
const _errs105 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.analysis_id !== undefined){
const _errs106 = errors;
if("inventor-cluster-flow.v1" !== data.analysis_id){
const err68 = {instancePath:instancePath+"/analysis_id",schemaPath:"#/anyOf/15/properties/analysis_id/const",keyword:"const",params:{allowedValue: "inventor-cluster-flow.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err68];
}
else {
vErrors.push(err68);
}
errors++;
}
var valid24 = _errs106 === errors;
}
else {
var valid24 = true;
}
if(valid24){
if(data.mark !== undefined){
const _errs107 = errors;
if("inventor-cluster-flow-svg.v1" !== data.mark){
const err69 = {instancePath:instancePath+"/mark",schemaPath:"#/anyOf/15/properties/mark/const",keyword:"const",params:{allowedValue: "inventor-cluster-flow-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err69];
}
else {
vErrors.push(err69);
}
errors++;
}
var valid24 = _errs107 === errors;
}
else {
var valid24 = true;
}
if(valid24){
if(data.title !== undefined){
const _errs108 = errors;
if("協働グループの変遷" !== data.title){
const err70 = {instancePath:instancePath+"/title",schemaPath:"#/anyOf/15/properties/title/const",keyword:"const",params:{allowedValue: "協働グループの変遷"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err70];
}
else {
vErrors.push(err70);
}
errors++;
}
var valid24 = _errs108 === errors;
}
else {
var valid24 = true;
}
if(valid24){
if(data.projection !== undefined){
const _errs109 = errors;
if(!(validate47(data.projection, {instancePath:instancePath+"/projection",parentData:data,parentDataProperty:"projection",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate47.errors : vErrors.concat(validate47.errors);
errors = vErrors.length;
}
var valid24 = _errs109 === errors;
}
else {
var valid24 = true;
}
}
}
}
}
var _valid0 = _errs105 === errors;
valid0 = valid0 || _valid0;
if(_valid0){
if(props0 !== true){
props0 = props0 || {};
props0.analysis_id = true;
props0.mark = true;
props0.title = true;
props0.projection = true;
}
}
const _errs110 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.analysis_id !== undefined){
const _errs111 = errors;
if("inventor-similarity.v1" !== data.analysis_id){
const err71 = {instancePath:instancePath+"/analysis_id",schemaPath:"#/anyOf/16/properties/analysis_id/const",keyword:"const",params:{allowedValue: "inventor-similarity.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err71];
}
else {
vErrors.push(err71);
}
errors++;
}
var valid25 = _errs111 === errors;
}
else {
var valid25 = true;
}
if(valid25){
if(data.mark !== undefined){
const _errs112 = errors;
if("inventor-similarity-svg.v1" !== data.mark){
const err72 = {instancePath:instancePath+"/mark",schemaPath:"#/anyOf/16/properties/mark/const",keyword:"const",params:{allowedValue: "inventor-similarity-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err72];
}
else {
vErrors.push(err72);
}
errors++;
}
var valid25 = _errs112 === errors;
}
else {
var valid25 = true;
}
if(valid25){
if(data.title !== undefined){
const _errs113 = errors;
if("発明者の技術類似度" !== data.title){
const err73 = {instancePath:instancePath+"/title",schemaPath:"#/anyOf/16/properties/title/const",keyword:"const",params:{allowedValue: "発明者の技術類似度"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err73];
}
else {
vErrors.push(err73);
}
errors++;
}
var valid25 = _errs113 === errors;
}
else {
var valid25 = true;
}
if(valid25){
if(data.projection !== undefined){
const _errs114 = errors;
if(!(validate49(data.projection, {instancePath:instancePath+"/projection",parentData:data,parentDataProperty:"projection",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate49.errors : vErrors.concat(validate49.errors);
errors = vErrors.length;
}
var valid25 = _errs114 === errors;
}
else {
var valid25 = true;
}
}
}
}
}
var _valid0 = _errs110 === errors;
valid0 = valid0 || _valid0;
if(_valid0){
if(props0 !== true){
props0 = props0 || {};
props0.analysis_id = true;
props0.mark = true;
props0.title = true;
props0.projection = true;
}
}
const _errs115 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.analysis_id !== undefined){
const _errs116 = errors;
if("inventor-impact.v1" !== data.analysis_id){
const err74 = {instancePath:instancePath+"/analysis_id",schemaPath:"#/anyOf/17/properties/analysis_id/const",keyword:"const",params:{allowedValue: "inventor-impact.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err74];
}
else {
vErrors.push(err74);
}
errors++;
}
var valid26 = _errs116 === errors;
}
else {
var valid26 = true;
}
if(valid26){
if(data.mark !== undefined){
const _errs117 = errors;
if("inventor-impact-svg.v1" !== data.mark){
const err75 = {instancePath:instancePath+"/mark",schemaPath:"#/anyOf/17/properties/mark/const",keyword:"const",params:{allowedValue: "inventor-impact-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err75];
}
else {
vErrors.push(err75);
}
errors++;
}
var valid26 = _errs117 === errors;
}
else {
var valid26 = true;
}
if(valid26){
if(data.title !== undefined){
const _errs118 = errors;
if("発明者の活動量と引用指標" !== data.title){
const err76 = {instancePath:instancePath+"/title",schemaPath:"#/anyOf/17/properties/title/const",keyword:"const",params:{allowedValue: "発明者の活動量と引用指標"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err76];
}
else {
vErrors.push(err76);
}
errors++;
}
var valid26 = _errs118 === errors;
}
else {
var valid26 = true;
}
if(valid26){
if(data.projection !== undefined){
const _errs119 = errors;
if(!(validate49(data.projection, {instancePath:instancePath+"/projection",parentData:data,parentDataProperty:"projection",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate49.errors : vErrors.concat(validate49.errors);
errors = vErrors.length;
}
var valid26 = _errs119 === errors;
}
else {
var valid26 = true;
}
}
}
}
}
var _valid0 = _errs115 === errors;
valid0 = valid0 || _valid0;
if(_valid0){
if(props0 !== true){
props0 = props0 || {};
props0.analysis_id = true;
props0.mark = true;
props0.title = true;
props0.projection = true;
}
}
const _errs120 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.analysis_id !== undefined){
const _errs121 = errors;
if("inventor-mobility.v1" !== data.analysis_id){
const err77 = {instancePath:instancePath+"/analysis_id",schemaPath:"#/anyOf/18/properties/analysis_id/const",keyword:"const",params:{allowedValue: "inventor-mobility.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err77];
}
else {
vErrors.push(err77);
}
errors++;
}
var valid27 = _errs121 === errors;
}
else {
var valid27 = true;
}
if(valid27){
if(data.mark !== undefined){
const _errs122 = errors;
if("inventor-mobility-svg.v1" !== data.mark){
const err78 = {instancePath:instancePath+"/mark",schemaPath:"#/anyOf/18/properties/mark/const",keyword:"const",params:{allowedValue: "inventor-mobility-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err78];
}
else {
vErrors.push(err78);
}
errors++;
}
var valid27 = _errs122 === errors;
}
else {
var valid27 = true;
}
if(valid27){
if(data.title !== undefined){
const _errs123 = errors;
if("発明者と企業の関係変化" !== data.title){
const err79 = {instancePath:instancePath+"/title",schemaPath:"#/anyOf/18/properties/title/const",keyword:"const",params:{allowedValue: "発明者と企業の関係変化"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err79];
}
else {
vErrors.push(err79);
}
errors++;
}
var valid27 = _errs123 === errors;
}
else {
var valid27 = true;
}
if(valid27){
if(data.projection !== undefined){
const _errs124 = errors;
if(!(validate45(data.projection, {instancePath:instancePath+"/projection",parentData:data,parentDataProperty:"projection",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate45.errors : vErrors.concat(validate45.errors);
errors = vErrors.length;
}
var valid27 = _errs124 === errors;
}
else {
var valid27 = true;
}
}
}
}
}
var _valid0 = _errs120 === errors;
valid0 = valid0 || _valid0;
if(_valid0){
if(props0 !== true){
props0 = props0 || {};
props0.analysis_id = true;
props0.mark = true;
props0.title = true;
props0.projection = true;
}
}
const _errs125 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
if(data.analysis_id !== undefined){
const _errs126 = errors;
if("inventor-mobility-flow.v1" !== data.analysis_id){
const err80 = {instancePath:instancePath+"/analysis_id",schemaPath:"#/anyOf/19/properties/analysis_id/const",keyword:"const",params:{allowedValue: "inventor-mobility-flow.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err80];
}
else {
vErrors.push(err80);
}
errors++;
}
var valid28 = _errs126 === errors;
}
else {
var valid28 = true;
}
if(valid28){
if(data.mark !== undefined){
const _errs127 = errors;
if("inventor-mobility-flow-svg.v1" !== data.mark){
const err81 = {instancePath:instancePath+"/mark",schemaPath:"#/anyOf/19/properties/mark/const",keyword:"const",params:{allowedValue: "inventor-mobility-flow-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err81];
}
else {
vErrors.push(err81);
}
errors++;
}
var valid28 = _errs127 === errors;
}
else {
var valid28 = true;
}
if(valid28){
if(data.title !== undefined){
const _errs128 = errors;
if("企業間の観測・移動フロー" !== data.title){
const err82 = {instancePath:instancePath+"/title",schemaPath:"#/anyOf/19/properties/title/const",keyword:"const",params:{allowedValue: "企業間の観測・移動フロー"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err82];
}
else {
vErrors.push(err82);
}
errors++;
}
var valid28 = _errs128 === errors;
}
else {
var valid28 = true;
}
if(valid28){
if(data.projection !== undefined){
let data97 = data.projection;
const _errs129 = errors;
if(!(validate40(data97, {instancePath:instancePath+"/projection",parentData:data,parentDataProperty:"projection",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate40.errors : vErrors.concat(validate40.errors);
errors = vErrors.length;
}
if(errors === _errs129){
if(data97 && typeof data97 == "object" && !Array.isArray(data97)){
if(data97.edges !== undefined){
let data98 = data97.edges;
const _errs131 = errors;
if(errors === _errs131){
if(Array.isArray(data98)){
var valid30 = true;
const len2 = data98.length;
for(let i2=0; i2<len2; i2++){
let data99 = data98[i2];
const _errs133 = errors;
if(errors === _errs133){
if(data99 && typeof data99 == "object" && !Array.isArray(data99)){
if(data99.directed !== undefined){
if(true !== data99.directed){
const err83 = {instancePath:instancePath+"/projection/edges/" + i2+"/directed",schemaPath:"#/anyOf/19/properties/projection/properties/edges/items/properties/directed/const",keyword:"const",params:{allowedValue: true},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err83];
}
else {
vErrors.push(err83);
}
errors++;
}
}
}
else {
const err84 = {instancePath:instancePath+"/projection/edges/" + i2,schemaPath:"#/anyOf/19/properties/projection/properties/edges/items/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err84];
}
else {
vErrors.push(err84);
}
errors++;
}
}
var valid30 = _errs133 === errors;
if(!valid30){
break;
}
}
}
else {
const err85 = {instancePath:instancePath+"/projection/edges",schemaPath:"#/anyOf/19/properties/projection/properties/edges/type",keyword:"type",params:{type: "array"},message:"must be array"};
if(vErrors === null){
vErrors = [err85];
}
else {
vErrors.push(err85);
}
errors++;
}
}
}
}
else {
const err86 = {instancePath:instancePath+"/projection",schemaPath:"#/anyOf/19/properties/projection/type",keyword:"type",params:{type: "object"},message:"must be object"};
if(vErrors === null){
vErrors = [err86];
}
else {
vErrors.push(err86);
}
errors++;
}
}
var valid28 = _errs129 === errors;
}
else {
var valid28 = true;
}
}
}
}
}
var _valid0 = _errs125 === errors;
valid0 = valid0 || _valid0;
if(_valid0){
if(props0 !== true){
props0 = props0 || {};
props0.analysis_id = true;
props0.mark = true;
props0.title = true;
props0.projection = true;
}
}
if(!valid0){
const err87 = {instancePath,schemaPath:"#/anyOf",keyword:"anyOf",params:{},message:"must match a schema in anyOf"};
if(vErrors === null){
vErrors = [err87];
}
else {
vErrors.push(err87);
}
errors++;
validate22.errors = vErrors;
return false;
}
else {
errors = _errs1;
if(vErrors !== null){
if(_errs1){
vErrors.length = _errs1;
}
else {
vErrors = null;
}
}
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((((((data.chart_model_contract_version === undefined) && (missing0 = "chart_model_contract_version")) || ((data.chart_type === undefined) && (missing0 = "chart_type"))) || ((data.analysis_id === undefined) && (missing0 = "analysis_id"))) || ((data.mark === undefined) && (missing0 = "mark"))) || ((data.title === undefined) && (missing0 = "title"))) || ((data.analysis_result_sha256 === undefined) && (missing0 = "analysis_result_sha256"))) || ((data.projection === undefined) && (missing0 = "projection"))) || ((data.population === undefined) && (missing0 = "population"))) || ((data.warnings === undefined) && (missing0 = "warnings"))){
validate22.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs136 = errors;
for(const key0 in data){
if(!(func84.call(schema33.properties, key0))){
validate22.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs136 === errors){
if(data.chart_model_contract_version !== undefined){
const _errs137 = errors;
if("1.0.0" !== data.chart_model_contract_version){
validate22.errors = [{instancePath:instancePath+"/chart_model_contract_version",schemaPath:"#/properties/chart_model_contract_version/const",keyword:"const",params:{allowedValue: "1.0.0"},message:"must be equal to constant"}];
return false;
}
var valid32 = _errs137 === errors;
}
else {
var valid32 = true;
}
if(valid32){
if(data.chart_type !== undefined){
const _errs138 = errors;
if("advanced.svg" !== data.chart_type){
validate22.errors = [{instancePath:instancePath+"/chart_type",schemaPath:"#/properties/chart_type/const",keyword:"const",params:{allowedValue: "advanced.svg"},message:"must be equal to constant"}];
return false;
}
var valid32 = _errs138 === errors;
}
else {
var valid32 = true;
}
if(valid32){
if(data.analysis_id !== undefined){
const _errs139 = errors;
if(typeof data.analysis_id !== "string"){
validate22.errors = [{instancePath:instancePath+"/analysis_id",schemaPath:"#/properties/analysis_id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid32 = _errs139 === errors;
}
else {
var valid32 = true;
}
if(valid32){
if(data.mark !== undefined){
const _errs141 = errors;
if(typeof data.mark !== "string"){
validate22.errors = [{instancePath:instancePath+"/mark",schemaPath:"#/properties/mark/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid32 = _errs141 === errors;
}
else {
var valid32 = true;
}
if(valid32){
if(data.title !== undefined){
const _errs143 = errors;
if(typeof data.title !== "string"){
validate22.errors = [{instancePath:instancePath+"/title",schemaPath:"#/properties/title/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid32 = _errs143 === errors;
}
else {
var valid32 = true;
}
if(valid32){
if(data.analysis_result_sha256 !== undefined){
let data106 = data.analysis_result_sha256;
const _errs145 = errors;
if(errors === _errs145){
if(typeof data106 === "string"){
if(!pattern5.test(data106)){
validate22.errors = [{instancePath:instancePath+"/analysis_result_sha256",schemaPath:"#/properties/analysis_result_sha256/pattern",keyword:"pattern",params:{pattern: "^[0-9a-f]{64}$"},message:"must match pattern \""+"^[0-9a-f]{64}$"+"\""}];
return false;
}
}
else {
validate22.errors = [{instancePath:instancePath+"/analysis_result_sha256",schemaPath:"#/properties/analysis_result_sha256/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid32 = _errs145 === errors;
}
else {
var valid32 = true;
}
if(valid32){
if(data.projection !== undefined){
let data107 = data.projection;
const _errs147 = errors;
if(!(data107 && typeof data107 == "object" && !Array.isArray(data107))){
validate22.errors = [{instancePath:instancePath+"/projection",schemaPath:"#/properties/projection/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
var valid32 = _errs147 === errors;
}
else {
var valid32 = true;
}
if(valid32){
if(data.population !== undefined){
let data108 = data.population;
const _errs149 = errors;
if(errors === _errs149){
if(data108 && typeof data108 == "object" && !Array.isArray(data108)){
let missing1;
if((((data108.input_rows === undefined) && (missing1 = "input_rows")) || ((data108.analyzed_rows === undefined) && (missing1 = "analyzed_rows"))) || ((data108.excluded_rows === undefined) && (missing1 = "excluded_rows"))){
validate22.errors = [{instancePath:instancePath+"/population",schemaPath:"#/properties/population/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
const _errs151 = errors;
for(const key1 in data108){
if(!(((key1 === "input_rows") || (key1 === "analyzed_rows")) || (key1 === "excluded_rows"))){
validate22.errors = [{instancePath:instancePath+"/population",schemaPath:"#/properties/population/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs151 === errors){
if(data108.input_rows !== undefined){
let data109 = data108.input_rows;
const _errs152 = errors;
if(!(((typeof data109 == "number") && (!(data109 % 1) && !isNaN(data109))) && (isFinite(data109)))){
validate22.errors = [{instancePath:instancePath+"/population/input_rows",schemaPath:"#/properties/population/properties/input_rows/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs152){
if((typeof data109 == "number") && (isFinite(data109))){
if(data109 > 10000000 || isNaN(data109)){
validate22.errors = [{instancePath:instancePath+"/population/input_rows",schemaPath:"#/properties/population/properties/input_rows/maximum",keyword:"maximum",params:{comparison: "<=", limit: 10000000},message:"must be <= 10000000"}];
return false;
}
else {
if(data109 < 0 || isNaN(data109)){
validate22.errors = [{instancePath:instancePath+"/population/input_rows",schemaPath:"#/properties/population/properties/input_rows/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid33 = _errs152 === errors;
}
else {
var valid33 = true;
}
if(valid33){
if(data108.analyzed_rows !== undefined){
let data110 = data108.analyzed_rows;
const _errs154 = errors;
if(!(((typeof data110 == "number") && (!(data110 % 1) && !isNaN(data110))) && (isFinite(data110)))){
validate22.errors = [{instancePath:instancePath+"/population/analyzed_rows",schemaPath:"#/properties/population/properties/analyzed_rows/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs154){
if((typeof data110 == "number") && (isFinite(data110))){
if(data110 > 10000000 || isNaN(data110)){
validate22.errors = [{instancePath:instancePath+"/population/analyzed_rows",schemaPath:"#/properties/population/properties/analyzed_rows/maximum",keyword:"maximum",params:{comparison: "<=", limit: 10000000},message:"must be <= 10000000"}];
return false;
}
else {
if(data110 < 0 || isNaN(data110)){
validate22.errors = [{instancePath:instancePath+"/population/analyzed_rows",schemaPath:"#/properties/population/properties/analyzed_rows/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid33 = _errs154 === errors;
}
else {
var valid33 = true;
}
if(valid33){
if(data108.excluded_rows !== undefined){
let data111 = data108.excluded_rows;
const _errs156 = errors;
if(!(((typeof data111 == "number") && (!(data111 % 1) && !isNaN(data111))) && (isFinite(data111)))){
validate22.errors = [{instancePath:instancePath+"/population/excluded_rows",schemaPath:"#/properties/population/properties/excluded_rows/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs156){
if((typeof data111 == "number") && (isFinite(data111))){
if(data111 > 10000000 || isNaN(data111)){
validate22.errors = [{instancePath:instancePath+"/population/excluded_rows",schemaPath:"#/properties/population/properties/excluded_rows/maximum",keyword:"maximum",params:{comparison: "<=", limit: 10000000},message:"must be <= 10000000"}];
return false;
}
else {
if(data111 < 0 || isNaN(data111)){
validate22.errors = [{instancePath:instancePath+"/population/excluded_rows",schemaPath:"#/properties/population/properties/excluded_rows/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid33 = _errs156 === errors;
}
else {
var valid33 = true;
}
}
}
}
}
}
else {
validate22.errors = [{instancePath:instancePath+"/population",schemaPath:"#/properties/population/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid32 = _errs149 === errors;
}
else {
var valid32 = true;
}
if(valid32){
if(data.warnings !== undefined){
let data112 = data.warnings;
const _errs158 = errors;
if(errors === _errs158){
if(Array.isArray(data112)){
if(data112.length > 100){
validate22.errors = [{instancePath:instancePath+"/warnings",schemaPath:"#/properties/warnings/maxItems",keyword:"maxItems",params:{limit: 100},message:"must NOT have more than 100 items"}];
return false;
}
else {
var valid34 = true;
const len3 = data112.length;
for(let i3=0; i3<len3; i3++){
let data113 = data112[i3];
const _errs160 = errors;
if(errors === _errs160){
if(typeof data113 === "string"){
if(func1(data113) > 4096){
validate22.errors = [{instancePath:instancePath+"/warnings/" + i3,schemaPath:"#/properties/warnings/items/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
}
else {
validate22.errors = [{instancePath:instancePath+"/warnings/" + i3,schemaPath:"#/properties/warnings/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid34 = _errs160 === errors;
if(!valid34){
break;
}
}
}
}
else {
validate22.errors = [{instancePath:instancePath+"/warnings",schemaPath:"#/properties/warnings/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid32 = _errs158 === errors;
}
else {
var valid32 = true;
}
}
}
}
}
}
}
}
}
}
}
}
else {
validate22.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate22.errors = vErrors;
return errors === 0;
}
validate22.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

export const validateSpecRaw = validate54;
const schema127 = {"$id":"urn:patent-analysis:advanced-render-spec:1.0.0","type":"object","additionalProperties":false,"required":["render_spec_contract_version","renderer_kind","locale","timezone","width","height","font_family","animation","axis_label_max_graphemes","echarts_version","render_profile_id"],"properties":{"render_spec_contract_version":{"const":"1.0.0"},"renderer_kind":{"const":"advanced.svg"},"locale":{"const":"ja-JP"},"palette":{"enum":["standard","colorblind","monochrome","high-contrast"]},"timezone":{"const":"UTC"},"width":{"const":1200},"height":{"const":675},"font_family":{"const":"Yu Gothic UI, Yu Gothic, Meiryo, sans-serif"},"animation":{"const":false},"axis_label_max_graphemes":{"const":28},"echarts_version":{"const":"6.1.0"},"render_profile_id":{"const":"advanced-svg-ja-jp-node22-echarts6.v1"}}};

function validate54(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
/*# sourceURL="urn:patent-analysis:advanced-render-spec:1.0.0" */;
let vErrors = null;
let errors = 0;
const evaluated0 = validate54.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((((((((data.render_spec_contract_version === undefined) && (missing0 = "render_spec_contract_version")) || ((data.renderer_kind === undefined) && (missing0 = "renderer_kind"))) || ((data.locale === undefined) && (missing0 = "locale"))) || ((data.timezone === undefined) && (missing0 = "timezone"))) || ((data.width === undefined) && (missing0 = "width"))) || ((data.height === undefined) && (missing0 = "height"))) || ((data.font_family === undefined) && (missing0 = "font_family"))) || ((data.animation === undefined) && (missing0 = "animation"))) || ((data.axis_label_max_graphemes === undefined) && (missing0 = "axis_label_max_graphemes"))) || ((data.echarts_version === undefined) && (missing0 = "echarts_version"))) || ((data.render_profile_id === undefined) && (missing0 = "render_profile_id"))){
validate54.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!(func84.call(schema127.properties, key0))){
validate54.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.render_spec_contract_version !== undefined){
const _errs2 = errors;
if("1.0.0" !== data.render_spec_contract_version){
validate54.errors = [{instancePath:instancePath+"/render_spec_contract_version",schemaPath:"#/properties/render_spec_contract_version/const",keyword:"const",params:{allowedValue: "1.0.0"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.renderer_kind !== undefined){
const _errs3 = errors;
if("advanced.svg" !== data.renderer_kind){
validate54.errors = [{instancePath:instancePath+"/renderer_kind",schemaPath:"#/properties/renderer_kind/const",keyword:"const",params:{allowedValue: "advanced.svg"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.locale !== undefined){
const _errs4 = errors;
if("ja-JP" !== data.locale){
validate54.errors = [{instancePath:instancePath+"/locale",schemaPath:"#/properties/locale/const",keyword:"const",params:{allowedValue: "ja-JP"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.palette !== undefined){
let data3 = data.palette;
const _errs5 = errors;
if(!((((data3 === "standard") || (data3 === "colorblind")) || (data3 === "monochrome")) || (data3 === "high-contrast"))){
validate54.errors = [{instancePath:instancePath+"/palette",schemaPath:"#/properties/palette/enum",keyword:"enum",params:{allowedValues: schema127.properties.palette.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.timezone !== undefined){
const _errs6 = errors;
if("UTC" !== data.timezone){
validate54.errors = [{instancePath:instancePath+"/timezone",schemaPath:"#/properties/timezone/const",keyword:"const",params:{allowedValue: "UTC"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs6 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.width !== undefined){
const _errs7 = errors;
if(1200 !== data.width){
validate54.errors = [{instancePath:instancePath+"/width",schemaPath:"#/properties/width/const",keyword:"const",params:{allowedValue: 1200},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs7 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.height !== undefined){
const _errs8 = errors;
if(675 !== data.height){
validate54.errors = [{instancePath:instancePath+"/height",schemaPath:"#/properties/height/const",keyword:"const",params:{allowedValue: 675},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs8 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.font_family !== undefined){
const _errs9 = errors;
if("Yu Gothic UI, Yu Gothic, Meiryo, sans-serif" !== data.font_family){
validate54.errors = [{instancePath:instancePath+"/font_family",schemaPath:"#/properties/font_family/const",keyword:"const",params:{allowedValue: "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs9 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.animation !== undefined){
const _errs10 = errors;
if(false !== data.animation){
validate54.errors = [{instancePath:instancePath+"/animation",schemaPath:"#/properties/animation/const",keyword:"const",params:{allowedValue: false},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs10 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.axis_label_max_graphemes !== undefined){
const _errs11 = errors;
if(28 !== data.axis_label_max_graphemes){
validate54.errors = [{instancePath:instancePath+"/axis_label_max_graphemes",schemaPath:"#/properties/axis_label_max_graphemes/const",keyword:"const",params:{allowedValue: 28},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs11 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.echarts_version !== undefined){
const _errs12 = errors;
if("6.1.0" !== data.echarts_version){
validate54.errors = [{instancePath:instancePath+"/echarts_version",schemaPath:"#/properties/echarts_version/const",keyword:"const",params:{allowedValue: "6.1.0"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs12 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.render_profile_id !== undefined){
const _errs13 = errors;
if("advanced-svg-ja-jp-node22-echarts6.v1" !== data.render_profile_id){
validate54.errors = [{instancePath:instancePath+"/render_profile_id",schemaPath:"#/properties/render_profile_id/const",keyword:"const",params:{allowedValue: "advanced-svg-ja-jp-node22-echarts6.v1"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs13 === errors;
}
else {
var valid0 = true;
}
}
}
}
}
}
}
}
}
}
}
}
}
}
}
else {
validate54.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate54.errors = vErrors;
return errors === 0;
}
validate54.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};
