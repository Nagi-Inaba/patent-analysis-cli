/* eslint-disable */
/* Generated validators enforce the closed points ChartModel contract. */
"use strict";
const validateRendererRequestRaw = validate20;
const schema31 = {"$id":"urn:patent-analysis:renderer-request:1.0.0","title":"RendererRequest 1.0.0","type":"object","additionalProperties":false,"required":["protocol_version","chart_model_b64","chart_model_sha256","render_spec_b64","render_spec_sha256"],"properties":{"protocol_version":{"const":"1.0.0"},"chart_model_b64":{"type":"string","minLength":4,"maxLength":2796204,"pattern":"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/][AQgw]==|[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=)?$"},"chart_model_sha256":{"type":"string","pattern":"^[0-9a-f]{64}$"},"render_spec_b64":{"type":"string","minLength":4,"maxLength":21848,"pattern":"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/][AQgw]==|[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=)?$"},"render_spec_sha256":{"type":"string","pattern":"^[0-9a-f]{64}$"}}};
function func1(value) {
  let length = 0;
  for (let index = 0; index < value.length; index += 1) {
    length += 1;
    const unit = value.charCodeAt(index);
    if (unit >= 0xD800 && unit <= 0xDBFF && index + 1 < value.length) {
      const next = value.charCodeAt(index + 1);
      if ((next & 0xFC00) === 0xDC00) index += 1;
    }
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

const validateRendererRuntimeRaw = validate21;
const schema32 = {"$id":"urn:patent-analysis:points-renderer-runtime:1.0.0","type":"object","additionalProperties":false,"required":["node_version","echarts_version","renderer_build_digest","render_profile_id"],"properties":{"node_version":{"const":"22.19.0"},"echarts_version":{"const":"6.1.0"},"renderer_build_digest":{"type":"string","pattern":"^[0-9a-f]{64}$"},"render_profile_id":{"const":"points-svg-ja-jp-node22-echarts6.v1"}}};

function validate21(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
/*# sourceURL="urn:patent-analysis:points-renderer-runtime:1.0.0" */;
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
if("points-svg-ja-jp-node22-echarts6.v1" !== data.render_profile_id){
validate21.errors = [{instancePath:instancePath+"/render_profile_id",schemaPath:"#/properties/render_profile_id/const",keyword:"const",params:{allowedValue: "points-svg-ja-jp-node22-echarts6.v1"},message:"must be equal to constant"}];
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

const validatePointsChartModelRaw = validate22;
const schema33 = {"$id":"urn:patent-analysis:points-chart-model:1.0.0","title":"Points ChartModel 1.0.0","type":"object","required":["chart_model_contract_version","chart_type","mark","analysis_result_sha256","title","x_axis","y_axis","size_axis","points","population","warnings"],"additionalProperties":false,"properties":{"chart_model_contract_version":{"const":"1.0.0"},"chart_type":{"const":"points.bubble"},"mark":{"const":"points-bubble-svg.v1"},"analysis_result_sha256":{"type":"string","pattern":"^[0-9a-f]{64}$"},"title":{"const":"技術ライフサイクル"},"x_axis":{"type":"object","required":["label","value_kind"],"additionalProperties":false,"properties":{"label":{"const":"ピーク年"},"value_kind":{"const":"year"}}},"y_axis":{"type":"object","required":["label","value_kind"],"additionalProperties":false,"properties":{"label":{"const":"CAGR（%）"},"value_kind":{"const":"number"}}},"size_axis":{"type":"object","required":["label","value_kind"],"additionalProperties":false,"properties":{"label":{"const":"総件数"},"value_kind":{"const":"count"}}},"points":{"type":"array","maxItems":20,"items":{"$ref":"#/$defs/point"}},"population":{"$ref":"#/$defs/population"},"warnings":{"type":"array","maxItems":100,"items":{"type":"string","maxLength":4096}}},"$defs":{"point":{"type":"object","required":["label","x","y","size","stage"],"additionalProperties":false,"properties":{"label":{"type":"string","minLength":1,"maxLength":4096},"x":{"type":"integer","minimum":1800,"maximum":2199},"y":{"type":"number"},"size":{"type":"integer","minimum":1,"maximum":1000000},"stage":{"enum":["growth","stable","slowing","decline"]}}},"population":{"type":"object","required":["input_rows","analyzed_rows","excluded_rows"],"additionalProperties":false,"properties":{"input_rows":{"type":"integer","minimum":0},"analyzed_rows":{"type":"integer","minimum":0},"excluded_rows":{"type":"integer","minimum":0}}}}};
const schema34 = {"type":"object","required":["label","x","y","size","stage"],"additionalProperties":false,"properties":{"label":{"type":"string","minLength":1,"maxLength":4096},"x":{"type":"integer","minimum":1800,"maximum":2199},"y":{"type":"number"},"size":{"type":"integer","minimum":1,"maximum":1000000},"stage":{"enum":["growth","stable","slowing","decline"]}}};
const schema35 = {"type":"object","required":["input_rows","analyzed_rows","excluded_rows"],"additionalProperties":false,"properties":{"input_rows":{"type":"integer","minimum":0},"analyzed_rows":{"type":"integer","minimum":0},"excluded_rows":{"type":"integer","minimum":0}}};
const func5 = Object.prototype.hasOwnProperty;

function validate22(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
/*# sourceURL="urn:patent-analysis:points-chart-model:1.0.0" */;
let vErrors = null;
let errors = 0;
const evaluated0 = validate22.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if((((((((((((data.chart_model_contract_version === undefined) && (missing0 = "chart_model_contract_version")) || ((data.chart_type === undefined) && (missing0 = "chart_type"))) || ((data.mark === undefined) && (missing0 = "mark"))) || ((data.analysis_result_sha256 === undefined) && (missing0 = "analysis_result_sha256"))) || ((data.title === undefined) && (missing0 = "title"))) || ((data.x_axis === undefined) && (missing0 = "x_axis"))) || ((data.y_axis === undefined) && (missing0 = "y_axis"))) || ((data.size_axis === undefined) && (missing0 = "size_axis"))) || ((data.points === undefined) && (missing0 = "points"))) || ((data.population === undefined) && (missing0 = "population"))) || ((data.warnings === undefined) && (missing0 = "warnings"))){
validate22.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!(func5.call(schema33.properties, key0))){
validate22.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.chart_model_contract_version !== undefined){
const _errs2 = errors;
if("1.0.0" !== data.chart_model_contract_version){
validate22.errors = [{instancePath:instancePath+"/chart_model_contract_version",schemaPath:"#/properties/chart_model_contract_version/const",keyword:"const",params:{allowedValue: "1.0.0"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.chart_type !== undefined){
const _errs3 = errors;
if("points.bubble" !== data.chart_type){
validate22.errors = [{instancePath:instancePath+"/chart_type",schemaPath:"#/properties/chart_type/const",keyword:"const",params:{allowedValue: "points.bubble"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.mark !== undefined){
const _errs4 = errors;
if("points-bubble-svg.v1" !== data.mark){
validate22.errors = [{instancePath:instancePath+"/mark",schemaPath:"#/properties/mark/const",keyword:"const",params:{allowedValue: "points-bubble-svg.v1"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.analysis_result_sha256 !== undefined){
let data3 = data.analysis_result_sha256;
const _errs5 = errors;
if(errors === _errs5){
if(typeof data3 === "string"){
if(!pattern5.test(data3)){
validate22.errors = [{instancePath:instancePath+"/analysis_result_sha256",schemaPath:"#/properties/analysis_result_sha256/pattern",keyword:"pattern",params:{pattern: "^[0-9a-f]{64}$"},message:"must match pattern \""+"^[0-9a-f]{64}$"+"\""}];
return false;
}
}
else {
validate22.errors = [{instancePath:instancePath+"/analysis_result_sha256",schemaPath:"#/properties/analysis_result_sha256/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.title !== undefined){
const _errs7 = errors;
if("技術ライフサイクル" !== data.title){
validate22.errors = [{instancePath:instancePath+"/title",schemaPath:"#/properties/title/const",keyword:"const",params:{allowedValue: "技術ライフサイクル"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs7 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.x_axis !== undefined){
let data5 = data.x_axis;
const _errs8 = errors;
if(errors === _errs8){
if(data5 && typeof data5 == "object" && !Array.isArray(data5)){
let missing1;
if(((data5.label === undefined) && (missing1 = "label")) || ((data5.value_kind === undefined) && (missing1 = "value_kind"))){
validate22.errors = [{instancePath:instancePath+"/x_axis",schemaPath:"#/properties/x_axis/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
const _errs10 = errors;
for(const key1 in data5){
if(!((key1 === "label") || (key1 === "value_kind"))){
validate22.errors = [{instancePath:instancePath+"/x_axis",schemaPath:"#/properties/x_axis/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs10 === errors){
if(data5.label !== undefined){
const _errs11 = errors;
if("ピーク年" !== data5.label){
validate22.errors = [{instancePath:instancePath+"/x_axis/label",schemaPath:"#/properties/x_axis/properties/label/const",keyword:"const",params:{allowedValue: "ピーク年"},message:"must be equal to constant"}];
return false;
}
var valid1 = _errs11 === errors;
}
else {
var valid1 = true;
}
if(valid1){
if(data5.value_kind !== undefined){
const _errs12 = errors;
if("year" !== data5.value_kind){
validate22.errors = [{instancePath:instancePath+"/x_axis/value_kind",schemaPath:"#/properties/x_axis/properties/value_kind/const",keyword:"const",params:{allowedValue: "year"},message:"must be equal to constant"}];
return false;
}
var valid1 = _errs12 === errors;
}
else {
var valid1 = true;
}
}
}
}
}
else {
validate22.errors = [{instancePath:instancePath+"/x_axis",schemaPath:"#/properties/x_axis/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid0 = _errs8 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.y_axis !== undefined){
let data8 = data.y_axis;
const _errs13 = errors;
if(errors === _errs13){
if(data8 && typeof data8 == "object" && !Array.isArray(data8)){
let missing2;
if(((data8.label === undefined) && (missing2 = "label")) || ((data8.value_kind === undefined) && (missing2 = "value_kind"))){
validate22.errors = [{instancePath:instancePath+"/y_axis",schemaPath:"#/properties/y_axis/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
const _errs15 = errors;
for(const key2 in data8){
if(!((key2 === "label") || (key2 === "value_kind"))){
validate22.errors = [{instancePath:instancePath+"/y_axis",schemaPath:"#/properties/y_axis/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key2},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs15 === errors){
if(data8.label !== undefined){
const _errs16 = errors;
if("CAGR（%）" !== data8.label){
validate22.errors = [{instancePath:instancePath+"/y_axis/label",schemaPath:"#/properties/y_axis/properties/label/const",keyword:"const",params:{allowedValue: "CAGR（%）"},message:"must be equal to constant"}];
return false;
}
var valid2 = _errs16 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data8.value_kind !== undefined){
const _errs17 = errors;
if("number" !== data8.value_kind){
validate22.errors = [{instancePath:instancePath+"/y_axis/value_kind",schemaPath:"#/properties/y_axis/properties/value_kind/const",keyword:"const",params:{allowedValue: "number"},message:"must be equal to constant"}];
return false;
}
var valid2 = _errs17 === errors;
}
else {
var valid2 = true;
}
}
}
}
}
else {
validate22.errors = [{instancePath:instancePath+"/y_axis",schemaPath:"#/properties/y_axis/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid0 = _errs13 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.size_axis !== undefined){
let data11 = data.size_axis;
const _errs18 = errors;
if(errors === _errs18){
if(data11 && typeof data11 == "object" && !Array.isArray(data11)){
let missing3;
if(((data11.label === undefined) && (missing3 = "label")) || ((data11.value_kind === undefined) && (missing3 = "value_kind"))){
validate22.errors = [{instancePath:instancePath+"/size_axis",schemaPath:"#/properties/size_axis/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"}];
return false;
}
else {
const _errs20 = errors;
for(const key3 in data11){
if(!((key3 === "label") || (key3 === "value_kind"))){
validate22.errors = [{instancePath:instancePath+"/size_axis",schemaPath:"#/properties/size_axis/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key3},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs20 === errors){
if(data11.label !== undefined){
const _errs21 = errors;
if("総件数" !== data11.label){
validate22.errors = [{instancePath:instancePath+"/size_axis/label",schemaPath:"#/properties/size_axis/properties/label/const",keyword:"const",params:{allowedValue: "総件数"},message:"must be equal to constant"}];
return false;
}
var valid3 = _errs21 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data11.value_kind !== undefined){
const _errs22 = errors;
if("count" !== data11.value_kind){
validate22.errors = [{instancePath:instancePath+"/size_axis/value_kind",schemaPath:"#/properties/size_axis/properties/value_kind/const",keyword:"const",params:{allowedValue: "count"},message:"must be equal to constant"}];
return false;
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
else {
validate22.errors = [{instancePath:instancePath+"/size_axis",schemaPath:"#/properties/size_axis/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid0 = _errs18 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.points !== undefined){
let data14 = data.points;
const _errs23 = errors;
if(errors === _errs23){
if(Array.isArray(data14)){
if(data14.length > 20){
validate22.errors = [{instancePath:instancePath+"/points",schemaPath:"#/properties/points/maxItems",keyword:"maxItems",params:{limit: 20},message:"must NOT have more than 20 items"}];
return false;
}
else {
var valid4 = true;
const len0 = data14.length;
for(let i0=0; i0<len0; i0++){
let data15 = data14[i0];
const _errs25 = errors;
const _errs26 = errors;
if(errors === _errs26){
if(data15 && typeof data15 == "object" && !Array.isArray(data15)){
let missing4;
if((((((data15.label === undefined) && (missing4 = "label")) || ((data15.x === undefined) && (missing4 = "x"))) || ((data15.y === undefined) && (missing4 = "y"))) || ((data15.size === undefined) && (missing4 = "size"))) || ((data15.stage === undefined) && (missing4 = "stage"))){
validate22.errors = [{instancePath:instancePath+"/points/" + i0,schemaPath:"#/$defs/point/required",keyword:"required",params:{missingProperty: missing4},message:"must have required property '"+missing4+"'"}];
return false;
}
else {
const _errs28 = errors;
for(const key4 in data15){
if(!(((((key4 === "label") || (key4 === "x")) || (key4 === "y")) || (key4 === "size")) || (key4 === "stage"))){
validate22.errors = [{instancePath:instancePath+"/points/" + i0,schemaPath:"#/$defs/point/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key4},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs28 === errors){
if(data15.label !== undefined){
let data16 = data15.label;
const _errs29 = errors;
if(errors === _errs29){
if(typeof data16 === "string"){
if(func1(data16) > 4096){
validate22.errors = [{instancePath:instancePath+"/points/" + i0+"/label",schemaPath:"#/$defs/point/properties/label/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data16) < 1){
validate22.errors = [{instancePath:instancePath+"/points/" + i0+"/label",schemaPath:"#/$defs/point/properties/label/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate22.errors = [{instancePath:instancePath+"/points/" + i0+"/label",schemaPath:"#/$defs/point/properties/label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid6 = _errs29 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data15.x !== undefined){
let data17 = data15.x;
const _errs31 = errors;
if(!(((typeof data17 == "number") && (!(data17 % 1) && !isNaN(data17))) && (isFinite(data17)))){
validate22.errors = [{instancePath:instancePath+"/points/" + i0+"/x",schemaPath:"#/$defs/point/properties/x/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs31){
if((typeof data17 == "number") && (isFinite(data17))){
if(data17 > 2199 || isNaN(data17)){
validate22.errors = [{instancePath:instancePath+"/points/" + i0+"/x",schemaPath:"#/$defs/point/properties/x/maximum",keyword:"maximum",params:{comparison: "<=", limit: 2199},message:"must be <= 2199"}];
return false;
}
else {
if(data17 < 1800 || isNaN(data17)){
validate22.errors = [{instancePath:instancePath+"/points/" + i0+"/x",schemaPath:"#/$defs/point/properties/x/minimum",keyword:"minimum",params:{comparison: ">=", limit: 1800},message:"must be >= 1800"}];
return false;
}
}
}
}
var valid6 = _errs31 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data15.y !== undefined){
let data18 = data15.y;
const _errs33 = errors;
if(!((typeof data18 == "number") && (isFinite(data18)))){
validate22.errors = [{instancePath:instancePath+"/points/" + i0+"/y",schemaPath:"#/$defs/point/properties/y/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
var valid6 = _errs33 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data15.size !== undefined){
let data19 = data15.size;
const _errs35 = errors;
if(!(((typeof data19 == "number") && (!(data19 % 1) && !isNaN(data19))) && (isFinite(data19)))){
validate22.errors = [{instancePath:instancePath+"/points/" + i0+"/size",schemaPath:"#/$defs/point/properties/size/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs35){
if((typeof data19 == "number") && (isFinite(data19))){
if(data19 > 1000000 || isNaN(data19)){
validate22.errors = [{instancePath:instancePath+"/points/" + i0+"/size",schemaPath:"#/$defs/point/properties/size/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1000000},message:"must be <= 1000000"}];
return false;
}
else {
if(data19 < 1 || isNaN(data19)){
validate22.errors = [{instancePath:instancePath+"/points/" + i0+"/size",schemaPath:"#/$defs/point/properties/size/minimum",keyword:"minimum",params:{comparison: ">=", limit: 1},message:"must be >= 1"}];
return false;
}
}
}
}
var valid6 = _errs35 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data15.stage !== undefined){
let data20 = data15.stage;
const _errs37 = errors;
if(!((((data20 === "growth") || (data20 === "stable")) || (data20 === "slowing")) || (data20 === "decline"))){
validate22.errors = [{instancePath:instancePath+"/points/" + i0+"/stage",schemaPath:"#/$defs/point/properties/stage/enum",keyword:"enum",params:{allowedValues: schema34.properties.stage.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid6 = _errs37 === errors;
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
else {
validate22.errors = [{instancePath:instancePath+"/points/" + i0,schemaPath:"#/$defs/point/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid4 = _errs25 === errors;
if(!valid4){
break;
}
}
}
}
else {
validate22.errors = [{instancePath:instancePath+"/points",schemaPath:"#/properties/points/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs23 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.population !== undefined){
let data21 = data.population;
const _errs38 = errors;
const _errs39 = errors;
if(errors === _errs39){
if(data21 && typeof data21 == "object" && !Array.isArray(data21)){
let missing5;
if((((data21.input_rows === undefined) && (missing5 = "input_rows")) || ((data21.analyzed_rows === undefined) && (missing5 = "analyzed_rows"))) || ((data21.excluded_rows === undefined) && (missing5 = "excluded_rows"))){
validate22.errors = [{instancePath:instancePath+"/population",schemaPath:"#/$defs/population/required",keyword:"required",params:{missingProperty: missing5},message:"must have required property '"+missing5+"'"}];
return false;
}
else {
const _errs41 = errors;
for(const key5 in data21){
if(!(((key5 === "input_rows") || (key5 === "analyzed_rows")) || (key5 === "excluded_rows"))){
validate22.errors = [{instancePath:instancePath+"/population",schemaPath:"#/$defs/population/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key5},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs41 === errors){
if(data21.input_rows !== undefined){
let data22 = data21.input_rows;
const _errs42 = errors;
if(!(((typeof data22 == "number") && (!(data22 % 1) && !isNaN(data22))) && (isFinite(data22)))){
validate22.errors = [{instancePath:instancePath+"/population/input_rows",schemaPath:"#/$defs/population/properties/input_rows/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs42){
if((typeof data22 == "number") && (isFinite(data22))){
if(data22 < 0 || isNaN(data22)){
validate22.errors = [{instancePath:instancePath+"/population/input_rows",schemaPath:"#/$defs/population/properties/input_rows/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid8 = _errs42 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data21.analyzed_rows !== undefined){
let data23 = data21.analyzed_rows;
const _errs44 = errors;
if(!(((typeof data23 == "number") && (!(data23 % 1) && !isNaN(data23))) && (isFinite(data23)))){
validate22.errors = [{instancePath:instancePath+"/population/analyzed_rows",schemaPath:"#/$defs/population/properties/analyzed_rows/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs44){
if((typeof data23 == "number") && (isFinite(data23))){
if(data23 < 0 || isNaN(data23)){
validate22.errors = [{instancePath:instancePath+"/population/analyzed_rows",schemaPath:"#/$defs/population/properties/analyzed_rows/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid8 = _errs44 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data21.excluded_rows !== undefined){
let data24 = data21.excluded_rows;
const _errs46 = errors;
if(!(((typeof data24 == "number") && (!(data24 % 1) && !isNaN(data24))) && (isFinite(data24)))){
validate22.errors = [{instancePath:instancePath+"/population/excluded_rows",schemaPath:"#/$defs/population/properties/excluded_rows/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs46){
if((typeof data24 == "number") && (isFinite(data24))){
if(data24 < 0 || isNaN(data24)){
validate22.errors = [{instancePath:instancePath+"/population/excluded_rows",schemaPath:"#/$defs/population/properties/excluded_rows/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid8 = _errs46 === errors;
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
validate22.errors = [{instancePath:instancePath+"/population",schemaPath:"#/$defs/population/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid0 = _errs38 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.warnings !== undefined){
let data25 = data.warnings;
const _errs48 = errors;
if(errors === _errs48){
if(Array.isArray(data25)){
if(data25.length > 100){
validate22.errors = [{instancePath:instancePath+"/warnings",schemaPath:"#/properties/warnings/maxItems",keyword:"maxItems",params:{limit: 100},message:"must NOT have more than 100 items"}];
return false;
}
else {
var valid9 = true;
const len1 = data25.length;
for(let i1=0; i1<len1; i1++){
let data26 = data25[i1];
const _errs50 = errors;
if(errors === _errs50){
if(typeof data26 === "string"){
if(func1(data26) > 4096){
validate22.errors = [{instancePath:instancePath+"/warnings/" + i1,schemaPath:"#/properties/warnings/items/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
}
else {
validate22.errors = [{instancePath:instancePath+"/warnings/" + i1,schemaPath:"#/properties/warnings/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid9 = _errs50 === errors;
if(!valid9){
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
var valid0 = _errs48 === errors;
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
else {
validate22.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate22.errors = vErrors;
return errors === 0;
}
validate22.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const validatePointsRenderSpecRaw = validate23;
const schema36 = {"$id":"urn:patent-analysis:points-render-spec:1.0.0","title":"Points RenderSpec 1.0.0","type":"object","required":["render_spec_contract_version","renderer_kind","locale","timezone","width","height","font_family","animation","axis_label_max_graphemes","echarts_version","render_profile_id"],"additionalProperties":false,"properties":{"render_spec_contract_version":{"const":"1.0.0"},"renderer_kind":{"const":"points.bubble.svg"},"locale":{"const":"ja-JP"},"timezone":{"const":"UTC"},"width":{"const":1200},"height":{"const":675},"font_family":{"const":"Yu Gothic UI, Yu Gothic, Meiryo, sans-serif"},"animation":{"const":false},"axis_label_max_graphemes":{"const":28},"echarts_version":{"const":"6.1.0"},"render_profile_id":{"const":"points-svg-ja-jp-node22-echarts6.v1"}}};

function validate23(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
/*# sourceURL="urn:patent-analysis:points-render-spec:1.0.0" */;
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
if((((((((((((data.render_spec_contract_version === undefined) && (missing0 = "render_spec_contract_version")) || ((data.renderer_kind === undefined) && (missing0 = "renderer_kind"))) || ((data.locale === undefined) && (missing0 = "locale"))) || ((data.timezone === undefined) && (missing0 = "timezone"))) || ((data.width === undefined) && (missing0 = "width"))) || ((data.height === undefined) && (missing0 = "height"))) || ((data.font_family === undefined) && (missing0 = "font_family"))) || ((data.animation === undefined) && (missing0 = "animation"))) || ((data.axis_label_max_graphemes === undefined) && (missing0 = "axis_label_max_graphemes"))) || ((data.echarts_version === undefined) && (missing0 = "echarts_version"))) || ((data.render_profile_id === undefined) && (missing0 = "render_profile_id"))){
validate23.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!(func5.call(schema36.properties, key0))){
validate23.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.render_spec_contract_version !== undefined){
const _errs2 = errors;
if("1.0.0" !== data.render_spec_contract_version){
validate23.errors = [{instancePath:instancePath+"/render_spec_contract_version",schemaPath:"#/properties/render_spec_contract_version/const",keyword:"const",params:{allowedValue: "1.0.0"},message:"must be equal to constant"}];
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
if("points.bubble.svg" !== data.renderer_kind){
validate23.errors = [{instancePath:instancePath+"/renderer_kind",schemaPath:"#/properties/renderer_kind/const",keyword:"const",params:{allowedValue: "points.bubble.svg"},message:"must be equal to constant"}];
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
validate23.errors = [{instancePath:instancePath+"/locale",schemaPath:"#/properties/locale/const",keyword:"const",params:{allowedValue: "ja-JP"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.timezone !== undefined){
const _errs5 = errors;
if("UTC" !== data.timezone){
validate23.errors = [{instancePath:instancePath+"/timezone",schemaPath:"#/properties/timezone/const",keyword:"const",params:{allowedValue: "UTC"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.width !== undefined){
const _errs6 = errors;
if(1200 !== data.width){
validate23.errors = [{instancePath:instancePath+"/width",schemaPath:"#/properties/width/const",keyword:"const",params:{allowedValue: 1200},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs6 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.height !== undefined){
const _errs7 = errors;
if(675 !== data.height){
validate23.errors = [{instancePath:instancePath+"/height",schemaPath:"#/properties/height/const",keyword:"const",params:{allowedValue: 675},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs7 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.font_family !== undefined){
const _errs8 = errors;
if("Yu Gothic UI, Yu Gothic, Meiryo, sans-serif" !== data.font_family){
validate23.errors = [{instancePath:instancePath+"/font_family",schemaPath:"#/properties/font_family/const",keyword:"const",params:{allowedValue: "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs8 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.animation !== undefined){
const _errs9 = errors;
if(false !== data.animation){
validate23.errors = [{instancePath:instancePath+"/animation",schemaPath:"#/properties/animation/const",keyword:"const",params:{allowedValue: false},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs9 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.axis_label_max_graphemes !== undefined){
const _errs10 = errors;
if(28 !== data.axis_label_max_graphemes){
validate23.errors = [{instancePath:instancePath+"/axis_label_max_graphemes",schemaPath:"#/properties/axis_label_max_graphemes/const",keyword:"const",params:{allowedValue: 28},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs10 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.echarts_version !== undefined){
const _errs11 = errors;
if("6.1.0" !== data.echarts_version){
validate23.errors = [{instancePath:instancePath+"/echarts_version",schemaPath:"#/properties/echarts_version/const",keyword:"const",params:{allowedValue: "6.1.0"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs11 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.render_profile_id !== undefined){
const _errs12 = errors;
if("points-svg-ja-jp-node22-echarts6.v1" !== data.render_profile_id){
validate23.errors = [{instancePath:instancePath+"/render_profile_id",schemaPath:"#/properties/render_profile_id/const",keyword:"const",params:{allowedValue: "points-svg-ja-jp-node22-echarts6.v1"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs12 === errors;
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
else {
validate23.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate23.errors = vErrors;
return errors === 0;
}
validate23.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const pointsSegmenter = new Intl.Segmenter("ja-JP", { granularity: "grapheme" });

function graphemeCount(value) {
  let count = 0;
  for (const _segment of pointsSegmenter.segment(value)) count += 1;
  return count;
}

function safeText(value) {
  if (value.normalize("NFC") !== value) return false;
  for (const character of value) {
    const codePoint = character.codePointAt(0);
    if (
      codePoint <= 0x1F ||
      (codePoint >= 0x7F && codePoint <= 0x9F) ||
      (codePoint >= 0xD800 && codePoint <= 0xDFFF) ||
      (codePoint >= 0xFDD0 && codePoint <= 0xFDEF) ||
      (codePoint & 0xFFFF) === 0xFFFE ||
      (codePoint & 0xFFFF) === 0xFFFF ||
      (codePoint >= 0x202A && codePoint <= 0x202E) ||
      (codePoint >= 0x2066 && codePoint <= 0x2069)
    ) return false;
  }
  return true;
}

export function validateRendererRequest(value) {
  return validateRendererRequestRaw(value);
}

export function validateRendererRuntime(value) {
  return validateRendererRuntimeRaw(value);
}

export function validateChartModel(value) {
  if (!validatePointsChartModelRaw(value) || !safeText(value.title)) return false;
  if (value.chart_type !== "points.bubble" || value.mark !== "points-bubble-svg.v1") return false;
  const labels = new Set();
  let displayGraphemes = graphemeCount(value.title);
  for (const point of value.points) {
    if (!safeText(point.label) || labels.has(point.label)) return false;
    labels.add(point.label);
    displayGraphemes += graphemeCount(point.label);
  }
  for (const warning of value.warnings) {
    if (!safeText(warning)) return false;
    displayGraphemes += graphemeCount(warning);
  }
  if (displayGraphemes > 20_000) return false;
  return value.population.input_rows === value.population.analyzed_rows + value.population.excluded_rows;
}

export function validateRenderSpec(value) {
  return validatePointsRenderSpecRaw(value);
}
