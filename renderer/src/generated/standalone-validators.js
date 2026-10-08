/* eslint-disable */
/*
 * Generated validators enforce authoritative Python ChartModel semantics.
 * The renderer-only NFC restriction is an explicit policy divergence:
 * Python accepts exactly derived NFD models, while SVG rendering rejects them without normalization.
 */
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
const schema32 = {"$id":"urn:patent-analysis:renderer-runtime:1.0.0","type":"object","additionalProperties":false,"required":["node_version","echarts_version","renderer_build_digest","render_profile_id"],"properties":{"node_version":{"const":"22.19.0"},"echarts_version":{"const":"6.1.0"},"renderer_build_digest":{"type":"string","pattern":"^[0-9a-f]{64}$"},"render_profile_id":{"const":"ranking-svg-ja-jp-node22-echarts6.v1"}}};

function validate21(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
/*# sourceURL="urn:patent-analysis:renderer-runtime:1.0.0" */;
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
if("ranking-svg-ja-jp-node22-echarts6.v1" !== data.render_profile_id){
validate21.errors = [{instancePath:instancePath+"/render_profile_id",schemaPath:"#/properties/render_profile_id/const",keyword:"const",params:{allowedValue: "ranking-svg-ja-jp-node22-echarts6.v1"},message:"must be equal to constant"}];
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

const validateChartModelRaw = validate22;
const schema33 = {"$id":"urn:patent-analysis:chart-model:1.0.0","type":"object","additionalProperties":false,"required":["chart_model_contract_version","chart_type","analysis_result_sha256","label_overlay_sha256","title","dimension","measure","population","rows","warnings"],"properties":{"chart_model_contract_version":{"const":"1.0.0"},"chart_type":{"const":"ranking.horizontal_bar"},"analysis_result_sha256":{"type":"string","pattern":"^[0-9a-f]{64}$"},"label_overlay_sha256":{"oneOf":[{"type":"string","pattern":"^[0-9a-f]{64}$"},{"type":"null"}]},"title":{"type":"string","minLength":1},"dimension":{"type":"object","additionalProperties":false,"required":["source_label","display_label","description"],"properties":{"source_label":{"type":"string","minLength":1,"maxLength":4096},"display_label":{"type":"string","minLength":1,"maxLength":4096},"description":{"type":["string","null"],"maxLength":4096}}},"measure":{"type":"object","additionalProperties":false,"required":["mode","column"],"properties":{"mode":{"enum":["count","sum","average","max","min"]},"column":{"oneOf":[{"type":"string","minLength":1,"maxLength":4096},{"type":"null"}]}},"allOf":[{"if":{"properties":{"mode":{"const":"count"}},"required":["mode"]},"then":{"properties":{"column":{"type":"null"}}},"else":{"properties":{"column":{"type":"string"}}}}]},"population":{"type":"object","additionalProperties":false,"required":["input_rows","analyzed_rows"],"properties":{"input_rows":{"type":"integer","minimum":0,"maximum":100000},"analyzed_rows":{"type":"integer","minimum":0,"maximum":500000}}},"rows":{"type":"array","minItems":0,"maxItems":101,"items":{"type":"object","additionalProperties":false,"required":["index","row_kind","source_label","display_label","description","semantic_label","value","count","share"],"properties":{"index":{"type":"integer","minimum":0,"maximum":100},"row_kind":{"enum":["dimension_value","remainder"]},"source_label":{"type":"string","minLength":1,"maxLength":4096},"display_label":{"type":"string","minLength":1,"maxLength":4096},"description":{"type":["string","null"],"maxLength":4096},"semantic_label":{"enum":["データ中の分類値","上位表示外の合計"]},"value":{"type":"number"},"count":{"type":"integer","minimum":1,"maximum":500000},"share":{"type":"number","minimum":0,"maximum":1}}}},"warnings":{"type":"array","minItems":0,"maxItems":32,"items":{"type":"string","minLength":0,"maxLength":4096}}}};
const func5 = Object.prototype.hasOwnProperty;

function validate22(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
/*# sourceURL="urn:patent-analysis:chart-model:1.0.0" */;
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
if(((((((((((data.chart_model_contract_version === undefined) && (missing0 = "chart_model_contract_version")) || ((data.chart_type === undefined) && (missing0 = "chart_type"))) || ((data.analysis_result_sha256 === undefined) && (missing0 = "analysis_result_sha256"))) || ((data.label_overlay_sha256 === undefined) && (missing0 = "label_overlay_sha256"))) || ((data.title === undefined) && (missing0 = "title"))) || ((data.dimension === undefined) && (missing0 = "dimension"))) || ((data.measure === undefined) && (missing0 = "measure"))) || ((data.population === undefined) && (missing0 = "population"))) || ((data.rows === undefined) && (missing0 = "rows"))) || ((data.warnings === undefined) && (missing0 = "warnings"))){
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
if("ranking.horizontal_bar" !== data.chart_type){
validate22.errors = [{instancePath:instancePath+"/chart_type",schemaPath:"#/properties/chart_type/const",keyword:"const",params:{allowedValue: "ranking.horizontal_bar"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.analysis_result_sha256 !== undefined){
let data2 = data.analysis_result_sha256;
const _errs4 = errors;
if(errors === _errs4){
if(typeof data2 === "string"){
if(!pattern5.test(data2)){
validate22.errors = [{instancePath:instancePath+"/analysis_result_sha256",schemaPath:"#/properties/analysis_result_sha256/pattern",keyword:"pattern",params:{pattern: "^[0-9a-f]{64}$"},message:"must match pattern \""+"^[0-9a-f]{64}$"+"\""}];
return false;
}
}
else {
validate22.errors = [{instancePath:instancePath+"/analysis_result_sha256",schemaPath:"#/properties/analysis_result_sha256/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.label_overlay_sha256 !== undefined){
let data3 = data.label_overlay_sha256;
const _errs6 = errors;
const _errs7 = errors;
let valid1 = false;
let passing0 = null;
const _errs8 = errors;
if(errors === _errs8){
if(typeof data3 === "string"){
if(!pattern5.test(data3)){
const err0 = {instancePath:instancePath+"/label_overlay_sha256",schemaPath:"#/properties/label_overlay_sha256/oneOf/0/pattern",keyword:"pattern",params:{pattern: "^[0-9a-f]{64}$"},message:"must match pattern \""+"^[0-9a-f]{64}$"+"\""};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
}
else {
const err1 = {instancePath:instancePath+"/label_overlay_sha256",schemaPath:"#/properties/label_overlay_sha256/oneOf/0/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
}
var _valid0 = _errs8 === errors;
if(_valid0){
valid1 = true;
passing0 = 0;
}
const _errs10 = errors;
if(data3 !== null){
const err2 = {instancePath:instancePath+"/label_overlay_sha256",schemaPath:"#/properties/label_overlay_sha256/oneOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
var _valid0 = _errs10 === errors;
if(_valid0 && valid1){
valid1 = false;
passing0 = [passing0, 1];
}
else {
if(_valid0){
valid1 = true;
passing0 = 1;
}
}
if(!valid1){
const err3 = {instancePath:instancePath+"/label_overlay_sha256",schemaPath:"#/properties/label_overlay_sha256/oneOf",keyword:"oneOf",params:{passingSchemas: passing0},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
validate22.errors = vErrors;
return false;
}
else {
errors = _errs7;
if(vErrors !== null){
if(_errs7){
vErrors.length = _errs7;
}
else {
vErrors = null;
}
}
}
var valid0 = _errs6 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.title !== undefined){
let data4 = data.title;
const _errs12 = errors;
if(errors === _errs12){
if(typeof data4 === "string"){
if(func1(data4) < 1){
validate22.errors = [{instancePath:instancePath+"/title",schemaPath:"#/properties/title/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
else {
validate22.errors = [{instancePath:instancePath+"/title",schemaPath:"#/properties/title/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs12 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.dimension !== undefined){
let data5 = data.dimension;
const _errs14 = errors;
if(errors === _errs14){
if(data5 && typeof data5 == "object" && !Array.isArray(data5)){
let missing1;
if((((data5.source_label === undefined) && (missing1 = "source_label")) || ((data5.display_label === undefined) && (missing1 = "display_label"))) || ((data5.description === undefined) && (missing1 = "description"))){
validate22.errors = [{instancePath:instancePath+"/dimension",schemaPath:"#/properties/dimension/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
const _errs16 = errors;
for(const key1 in data5){
if(!(((key1 === "source_label") || (key1 === "display_label")) || (key1 === "description"))){
validate22.errors = [{instancePath:instancePath+"/dimension",schemaPath:"#/properties/dimension/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs16 === errors){
if(data5.source_label !== undefined){
let data6 = data5.source_label;
const _errs17 = errors;
if(errors === _errs17){
if(typeof data6 === "string"){
if(func1(data6) > 4096){
validate22.errors = [{instancePath:instancePath+"/dimension/source_label",schemaPath:"#/properties/dimension/properties/source_label/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data6) < 1){
validate22.errors = [{instancePath:instancePath+"/dimension/source_label",schemaPath:"#/properties/dimension/properties/source_label/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate22.errors = [{instancePath:instancePath+"/dimension/source_label",schemaPath:"#/properties/dimension/properties/source_label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid2 = _errs17 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data5.display_label !== undefined){
let data7 = data5.display_label;
const _errs19 = errors;
if(errors === _errs19){
if(typeof data7 === "string"){
if(func1(data7) > 4096){
validate22.errors = [{instancePath:instancePath+"/dimension/display_label",schemaPath:"#/properties/dimension/properties/display_label/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data7) < 1){
validate22.errors = [{instancePath:instancePath+"/dimension/display_label",schemaPath:"#/properties/dimension/properties/display_label/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate22.errors = [{instancePath:instancePath+"/dimension/display_label",schemaPath:"#/properties/dimension/properties/display_label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid2 = _errs19 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data5.description !== undefined){
let data8 = data5.description;
const _errs21 = errors;
if((typeof data8 !== "string") && (data8 !== null)){
validate22.errors = [{instancePath:instancePath+"/dimension/description",schemaPath:"#/properties/dimension/properties/description/type",keyword:"type",params:{type: schema33.properties.dimension.properties.description.type},message:"must be string,null"}];
return false;
}
if(errors === _errs21){
if(typeof data8 === "string"){
if(func1(data8) > 4096){
validate22.errors = [{instancePath:instancePath+"/dimension/description",schemaPath:"#/properties/dimension/properties/description/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
}
}
var valid2 = _errs21 === errors;
}
else {
var valid2 = true;
}
}
}
}
}
}
else {
validate22.errors = [{instancePath:instancePath+"/dimension",schemaPath:"#/properties/dimension/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid0 = _errs14 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.measure !== undefined){
let data9 = data.measure;
const _errs23 = errors;
const _errs26 = errors;
let valid4 = true;
const _errs27 = errors;
if(data9 && typeof data9 == "object" && !Array.isArray(data9)){
let missing2;
if((data9.mode === undefined) && (missing2 = "mode")){
const err4 = {};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
else {
if(data9.mode !== undefined){
if("count" !== data9.mode){
const err5 = {};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
}
}
}
var _valid1 = _errs27 === errors;
errors = _errs26;
if(vErrors !== null){
if(_errs26){
vErrors.length = _errs26;
}
else {
vErrors = null;
}
}
let ifClause0;
if(_valid1){
const _errs29 = errors;
if(data9 && typeof data9 == "object" && !Array.isArray(data9)){
if(data9.column !== undefined){
if(data9.column !== null){
validate22.errors = [{instancePath:instancePath+"/measure/column",schemaPath:"#/properties/measure/allOf/0/then/properties/column/type",keyword:"type",params:{type: "null"},message:"must be null"}];
return false;
}
}
}
var _valid1 = _errs29 === errors;
valid4 = _valid1;
if(valid4){
var props0 = {};
props0.column = true;
props0.mode = true;
}
ifClause0 = "then";
}
else {
const _errs32 = errors;
if(data9 && typeof data9 == "object" && !Array.isArray(data9)){
if(data9.column !== undefined){
if(typeof data9.column !== "string"){
validate22.errors = [{instancePath:instancePath+"/measure/column",schemaPath:"#/properties/measure/allOf/0/else/properties/column/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
}
var _valid1 = _errs32 === errors;
valid4 = _valid1;
if(valid4){
if(props0 !== true){
props0 = props0 || {};
props0.column = true;
}
}
ifClause0 = "else";
}
if(!valid4){
const err6 = {instancePath:instancePath+"/measure",schemaPath:"#/properties/measure/allOf/0/if",keyword:"if",params:{failingKeyword: ifClause0},message:"must match \""+ifClause0+"\" schema"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
validate22.errors = vErrors;
return false;
}
if(errors === _errs23){
if(data9 && typeof data9 == "object" && !Array.isArray(data9)){
let missing3;
if(((data9.mode === undefined) && (missing3 = "mode")) || ((data9.column === undefined) && (missing3 = "column"))){
validate22.errors = [{instancePath:instancePath+"/measure",schemaPath:"#/properties/measure/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"}];
return false;
}
else {
const _errs35 = errors;
for(const key2 in data9){
if(!((key2 === "mode") || (key2 === "column"))){
validate22.errors = [{instancePath:instancePath+"/measure",schemaPath:"#/properties/measure/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key2},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs35 === errors){
if(data9.mode !== undefined){
let data13 = data9.mode;
const _errs36 = errors;
if(!(((((data13 === "count") || (data13 === "sum")) || (data13 === "average")) || (data13 === "max")) || (data13 === "min"))){
validate22.errors = [{instancePath:instancePath+"/measure/mode",schemaPath:"#/properties/measure/properties/mode/enum",keyword:"enum",params:{allowedValues: schema33.properties.measure.properties.mode.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid8 = _errs36 === errors;
}
else {
var valid8 = true;
}
if(valid8){
if(data9.column !== undefined){
let data14 = data9.column;
const _errs37 = errors;
const _errs38 = errors;
let valid9 = false;
let passing1 = null;
const _errs39 = errors;
if(errors === _errs39){
if(typeof data14 === "string"){
if(func1(data14) > 4096){
const err7 = {instancePath:instancePath+"/measure/column",schemaPath:"#/properties/measure/properties/column/oneOf/0/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"};
if(vErrors === null){
vErrors = [err7];
}
else {
vErrors.push(err7);
}
errors++;
}
else {
if(func1(data14) < 1){
const err8 = {instancePath:instancePath+"/measure/column",schemaPath:"#/properties/measure/properties/column/oneOf/0/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"};
if(vErrors === null){
vErrors = [err8];
}
else {
vErrors.push(err8);
}
errors++;
}
}
}
else {
const err9 = {instancePath:instancePath+"/measure/column",schemaPath:"#/properties/measure/properties/column/oneOf/0/type",keyword:"type",params:{type: "string"},message:"must be string"};
if(vErrors === null){
vErrors = [err9];
}
else {
vErrors.push(err9);
}
errors++;
}
}
var _valid2 = _errs39 === errors;
if(_valid2){
valid9 = true;
passing1 = 0;
}
const _errs41 = errors;
if(data14 !== null){
const err10 = {instancePath:instancePath+"/measure/column",schemaPath:"#/properties/measure/properties/column/oneOf/1/type",keyword:"type",params:{type: "null"},message:"must be null"};
if(vErrors === null){
vErrors = [err10];
}
else {
vErrors.push(err10);
}
errors++;
}
var _valid2 = _errs41 === errors;
if(_valid2 && valid9){
valid9 = false;
passing1 = [passing1, 1];
}
else {
if(_valid2){
valid9 = true;
passing1 = 1;
}
}
if(!valid9){
const err11 = {instancePath:instancePath+"/measure/column",schemaPath:"#/properties/measure/properties/column/oneOf",keyword:"oneOf",params:{passingSchemas: passing1},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err11];
}
else {
vErrors.push(err11);
}
errors++;
validate22.errors = vErrors;
return false;
}
else {
errors = _errs38;
if(vErrors !== null){
if(_errs38){
vErrors.length = _errs38;
}
else {
vErrors = null;
}
}
}
var valid8 = _errs37 === errors;
}
else {
var valid8 = true;
}
}
}
}
}
else {
validate22.errors = [{instancePath:instancePath+"/measure",schemaPath:"#/properties/measure/type",keyword:"type",params:{type: "object"},message:"must be object"}];
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
let data15 = data.population;
const _errs43 = errors;
if(errors === _errs43){
if(data15 && typeof data15 == "object" && !Array.isArray(data15)){
let missing4;
if(((data15.input_rows === undefined) && (missing4 = "input_rows")) || ((data15.analyzed_rows === undefined) && (missing4 = "analyzed_rows"))){
validate22.errors = [{instancePath:instancePath+"/population",schemaPath:"#/properties/population/required",keyword:"required",params:{missingProperty: missing4},message:"must have required property '"+missing4+"'"}];
return false;
}
else {
const _errs45 = errors;
for(const key3 in data15){
if(!((key3 === "input_rows") || (key3 === "analyzed_rows"))){
validate22.errors = [{instancePath:instancePath+"/population",schemaPath:"#/properties/population/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key3},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs45 === errors){
if(data15.input_rows !== undefined){
let data16 = data15.input_rows;
const _errs46 = errors;
if(!(((typeof data16 == "number") && (!(data16 % 1) && !isNaN(data16))) && (isFinite(data16)))){
validate22.errors = [{instancePath:instancePath+"/population/input_rows",schemaPath:"#/properties/population/properties/input_rows/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs46){
if((typeof data16 == "number") && (isFinite(data16))){
if(data16 > 100000 || isNaN(data16)){
validate22.errors = [{instancePath:instancePath+"/population/input_rows",schemaPath:"#/properties/population/properties/input_rows/maximum",keyword:"maximum",params:{comparison: "<=", limit: 100000},message:"must be <= 100000"}];
return false;
}
else {
if(data16 < 0 || isNaN(data16)){
validate22.errors = [{instancePath:instancePath+"/population/input_rows",schemaPath:"#/properties/population/properties/input_rows/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid10 = _errs46 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.analyzed_rows !== undefined){
let data17 = data15.analyzed_rows;
const _errs48 = errors;
if(!(((typeof data17 == "number") && (!(data17 % 1) && !isNaN(data17))) && (isFinite(data17)))){
validate22.errors = [{instancePath:instancePath+"/population/analyzed_rows",schemaPath:"#/properties/population/properties/analyzed_rows/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs48){
if((typeof data17 == "number") && (isFinite(data17))){
if(data17 > 500000 || isNaN(data17)){
validate22.errors = [{instancePath:instancePath+"/population/analyzed_rows",schemaPath:"#/properties/population/properties/analyzed_rows/maximum",keyword:"maximum",params:{comparison: "<=", limit: 500000},message:"must be <= 500000"}];
return false;
}
else {
if(data17 < 0 || isNaN(data17)){
validate22.errors = [{instancePath:instancePath+"/population/analyzed_rows",schemaPath:"#/properties/population/properties/analyzed_rows/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid10 = _errs48 === errors;
}
else {
var valid10 = true;
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
var valid0 = _errs43 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.rows !== undefined){
let data18 = data.rows;
const _errs50 = errors;
if(errors === _errs50){
if(Array.isArray(data18)){
if(data18.length > 101){
validate22.errors = [{instancePath:instancePath+"/rows",schemaPath:"#/properties/rows/maxItems",keyword:"maxItems",params:{limit: 101},message:"must NOT have more than 101 items"}];
return false;
}
else {
if(data18.length < 0){
validate22.errors = [{instancePath:instancePath+"/rows",schemaPath:"#/properties/rows/minItems",keyword:"minItems",params:{limit: 0},message:"must NOT have fewer than 0 items"}];
return false;
}
else {
var valid11 = true;
const len0 = data18.length;
for(let i0=0; i0<len0; i0++){
let data19 = data18[i0];
const _errs52 = errors;
if(errors === _errs52){
if(data19 && typeof data19 == "object" && !Array.isArray(data19)){
let missing5;
if((((((((((data19.index === undefined) && (missing5 = "index")) || ((data19.row_kind === undefined) && (missing5 = "row_kind"))) || ((data19.source_label === undefined) && (missing5 = "source_label"))) || ((data19.display_label === undefined) && (missing5 = "display_label"))) || ((data19.description === undefined) && (missing5 = "description"))) || ((data19.semantic_label === undefined) && (missing5 = "semantic_label"))) || ((data19.value === undefined) && (missing5 = "value"))) || ((data19.count === undefined) && (missing5 = "count"))) || ((data19.share === undefined) && (missing5 = "share"))){
validate22.errors = [{instancePath:instancePath+"/rows/" + i0,schemaPath:"#/properties/rows/items/required",keyword:"required",params:{missingProperty: missing5},message:"must have required property '"+missing5+"'"}];
return false;
}
else {
const _errs54 = errors;
for(const key4 in data19){
if(!(func5.call(schema33.properties.rows.items.properties, key4))){
validate22.errors = [{instancePath:instancePath+"/rows/" + i0,schemaPath:"#/properties/rows/items/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key4},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs54 === errors){
if(data19.index !== undefined){
let data20 = data19.index;
const _errs55 = errors;
if(!(((typeof data20 == "number") && (!(data20 % 1) && !isNaN(data20))) && (isFinite(data20)))){
validate22.errors = [{instancePath:instancePath+"/rows/" + i0+"/index",schemaPath:"#/properties/rows/items/properties/index/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs55){
if((typeof data20 == "number") && (isFinite(data20))){
if(data20 > 100 || isNaN(data20)){
validate22.errors = [{instancePath:instancePath+"/rows/" + i0+"/index",schemaPath:"#/properties/rows/items/properties/index/maximum",keyword:"maximum",params:{comparison: "<=", limit: 100},message:"must be <= 100"}];
return false;
}
else {
if(data20 < 0 || isNaN(data20)){
validate22.errors = [{instancePath:instancePath+"/rows/" + i0+"/index",schemaPath:"#/properties/rows/items/properties/index/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid12 = _errs55 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data19.row_kind !== undefined){
let data21 = data19.row_kind;
const _errs57 = errors;
if(!((data21 === "dimension_value") || (data21 === "remainder"))){
validate22.errors = [{instancePath:instancePath+"/rows/" + i0+"/row_kind",schemaPath:"#/properties/rows/items/properties/row_kind/enum",keyword:"enum",params:{allowedValues: schema33.properties.rows.items.properties.row_kind.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid12 = _errs57 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data19.source_label !== undefined){
let data22 = data19.source_label;
const _errs58 = errors;
if(errors === _errs58){
if(typeof data22 === "string"){
if(func1(data22) > 4096){
validate22.errors = [{instancePath:instancePath+"/rows/" + i0+"/source_label",schemaPath:"#/properties/rows/items/properties/source_label/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data22) < 1){
validate22.errors = [{instancePath:instancePath+"/rows/" + i0+"/source_label",schemaPath:"#/properties/rows/items/properties/source_label/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate22.errors = [{instancePath:instancePath+"/rows/" + i0+"/source_label",schemaPath:"#/properties/rows/items/properties/source_label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid12 = _errs58 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data19.display_label !== undefined){
let data23 = data19.display_label;
const _errs60 = errors;
if(errors === _errs60){
if(typeof data23 === "string"){
if(func1(data23) > 4096){
validate22.errors = [{instancePath:instancePath+"/rows/" + i0+"/display_label",schemaPath:"#/properties/rows/items/properties/display_label/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data23) < 1){
validate22.errors = [{instancePath:instancePath+"/rows/" + i0+"/display_label",schemaPath:"#/properties/rows/items/properties/display_label/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate22.errors = [{instancePath:instancePath+"/rows/" + i0+"/display_label",schemaPath:"#/properties/rows/items/properties/display_label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid12 = _errs60 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data19.description !== undefined){
let data24 = data19.description;
const _errs62 = errors;
if((typeof data24 !== "string") && (data24 !== null)){
validate22.errors = [{instancePath:instancePath+"/rows/" + i0+"/description",schemaPath:"#/properties/rows/items/properties/description/type",keyword:"type",params:{type: schema33.properties.rows.items.properties.description.type},message:"must be string,null"}];
return false;
}
if(errors === _errs62){
if(typeof data24 === "string"){
if(func1(data24) > 4096){
validate22.errors = [{instancePath:instancePath+"/rows/" + i0+"/description",schemaPath:"#/properties/rows/items/properties/description/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
}
}
var valid12 = _errs62 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data19.semantic_label !== undefined){
let data25 = data19.semantic_label;
const _errs64 = errors;
if(!((data25 === "データ中の分類値") || (data25 === "上位表示外の合計"))){
validate22.errors = [{instancePath:instancePath+"/rows/" + i0+"/semantic_label",schemaPath:"#/properties/rows/items/properties/semantic_label/enum",keyword:"enum",params:{allowedValues: schema33.properties.rows.items.properties.semantic_label.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid12 = _errs64 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data19.value !== undefined){
let data26 = data19.value;
const _errs65 = errors;
if(!((typeof data26 == "number") && (isFinite(data26)))){
validate22.errors = [{instancePath:instancePath+"/rows/" + i0+"/value",schemaPath:"#/properties/rows/items/properties/value/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
var valid12 = _errs65 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data19.count !== undefined){
let data27 = data19.count;
const _errs67 = errors;
if(!(((typeof data27 == "number") && (!(data27 % 1) && !isNaN(data27))) && (isFinite(data27)))){
validate22.errors = [{instancePath:instancePath+"/rows/" + i0+"/count",schemaPath:"#/properties/rows/items/properties/count/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs67){
if((typeof data27 == "number") && (isFinite(data27))){
if(data27 > 500000 || isNaN(data27)){
validate22.errors = [{instancePath:instancePath+"/rows/" + i0+"/count",schemaPath:"#/properties/rows/items/properties/count/maximum",keyword:"maximum",params:{comparison: "<=", limit: 500000},message:"must be <= 500000"}];
return false;
}
else {
if(data27 < 1 || isNaN(data27)){
validate22.errors = [{instancePath:instancePath+"/rows/" + i0+"/count",schemaPath:"#/properties/rows/items/properties/count/minimum",keyword:"minimum",params:{comparison: ">=", limit: 1},message:"must be >= 1"}];
return false;
}
}
}
}
var valid12 = _errs67 === errors;
}
else {
var valid12 = true;
}
if(valid12){
if(data19.share !== undefined){
let data28 = data19.share;
const _errs69 = errors;
if(errors === _errs69){
if((typeof data28 == "number") && (isFinite(data28))){
if(data28 > 1 || isNaN(data28)){
validate22.errors = [{instancePath:instancePath+"/rows/" + i0+"/share",schemaPath:"#/properties/rows/items/properties/share/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1},message:"must be <= 1"}];
return false;
}
else {
if(data28 < 0 || isNaN(data28)){
validate22.errors = [{instancePath:instancePath+"/rows/" + i0+"/share",schemaPath:"#/properties/rows/items/properties/share/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
else {
validate22.errors = [{instancePath:instancePath+"/rows/" + i0+"/share",schemaPath:"#/properties/rows/items/properties/share/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid12 = _errs69 === errors;
}
else {
var valid12 = true;
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
validate22.errors = [{instancePath:instancePath+"/rows/" + i0,schemaPath:"#/properties/rows/items/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid11 = _errs52 === errors;
if(!valid11){
break;
}
}
}
}
}
else {
validate22.errors = [{instancePath:instancePath+"/rows",schemaPath:"#/properties/rows/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs50 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.warnings !== undefined){
let data29 = data.warnings;
const _errs71 = errors;
if(errors === _errs71){
if(Array.isArray(data29)){
if(data29.length > 32){
validate22.errors = [{instancePath:instancePath+"/warnings",schemaPath:"#/properties/warnings/maxItems",keyword:"maxItems",params:{limit: 32},message:"must NOT have more than 32 items"}];
return false;
}
else {
if(data29.length < 0){
validate22.errors = [{instancePath:instancePath+"/warnings",schemaPath:"#/properties/warnings/minItems",keyword:"minItems",params:{limit: 0},message:"must NOT have fewer than 0 items"}];
return false;
}
else {
var valid13 = true;
const len1 = data29.length;
for(let i1=0; i1<len1; i1++){
let data30 = data29[i1];
const _errs73 = errors;
if(errors === _errs73){
if(typeof data30 === "string"){
if(func1(data30) > 4096){
validate22.errors = [{instancePath:instancePath+"/warnings/" + i1,schemaPath:"#/properties/warnings/items/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data30) < 0){
validate22.errors = [{instancePath:instancePath+"/warnings/" + i1,schemaPath:"#/properties/warnings/items/minLength",keyword:"minLength",params:{limit: 0},message:"must NOT have fewer than 0 characters"}];
return false;
}
}
}
else {
validate22.errors = [{instancePath:instancePath+"/warnings/" + i1,schemaPath:"#/properties/warnings/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid13 = _errs73 === errors;
if(!valid13){
break;
}
}
}
}
}
else {
validate22.errors = [{instancePath:instancePath+"/warnings",schemaPath:"#/properties/warnings/type",keyword:"type",params:{type: "array"},message:"must be array"}];
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

const validateRenderSpecRaw = validate23;
const schema34 = {"$id":"urn:patent-analysis:render-spec:1.0.0","type":"object","additionalProperties":false,"required":["render_spec_contract_version","renderer_kind","locale","timezone","width","height","font_family","animation","axis_label_max_graphemes","echarts_version","render_profile_id"],"properties":{"render_spec_contract_version":{"const":"1.0.0"},"renderer_kind":{"const":"ranking.horizontal_bar.svg"},"locale":{"const":"ja-JP"},"timezone":{"const":"UTC"},"width":{"const":1200},"height":{"type":"integer","minimum":675,"maximum":4096},"font_family":{"const":"Yu Gothic UI, Yu Gothic, Meiryo, sans-serif"},"animation":{"const":false},"axis_label_max_graphemes":{"const":28},"echarts_version":{"const":"6.1.0"},"render_profile_id":{"const":"ranking-svg-ja-jp-node22-echarts6.v1"}}};

function validate23(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
/*# sourceURL="urn:patent-analysis:render-spec:1.0.0" */;
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
if(!(func5.call(schema34.properties, key0))){
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
if("ranking.horizontal_bar.svg" !== data.renderer_kind){
validate23.errors = [{instancePath:instancePath+"/renderer_kind",schemaPath:"#/properties/renderer_kind/const",keyword:"const",params:{allowedValue: "ranking.horizontal_bar.svg"},message:"must be equal to constant"}];
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
let data5 = data.height;
const _errs7 = errors;
if(!(((typeof data5 == "number") && (!(data5 % 1) && !isNaN(data5))) && (isFinite(data5)))){
validate23.errors = [{instancePath:instancePath+"/height",schemaPath:"#/properties/height/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs7){
if((typeof data5 == "number") && (isFinite(data5))){
if(data5 > 4096 || isNaN(data5)){
validate23.errors = [{instancePath:instancePath+"/height",schemaPath:"#/properties/height/maximum",keyword:"maximum",params:{comparison: "<=", limit: 4096},message:"must be <= 4096"}];
return false;
}
else {
if(data5 < 675 || isNaN(data5)){
validate23.errors = [{instancePath:instancePath+"/height",schemaPath:"#/properties/height/minimum",keyword:"minimum",params:{comparison: ">=", limit: 675},message:"must be >= 675"}];
return false;
}
}
}
}
var valid0 = _errs7 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.font_family !== undefined){
const _errs9 = errors;
if("Yu Gothic UI, Yu Gothic, Meiryo, sans-serif" !== data.font_family){
validate23.errors = [{instancePath:instancePath+"/font_family",schemaPath:"#/properties/font_family/const",keyword:"const",params:{allowedValue: "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif"},message:"must be equal to constant"}];
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
validate23.errors = [{instancePath:instancePath+"/animation",schemaPath:"#/properties/animation/const",keyword:"const",params:{allowedValue: false},message:"must be equal to constant"}];
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
validate23.errors = [{instancePath:instancePath+"/axis_label_max_graphemes",schemaPath:"#/properties/axis_label_max_graphemes/const",keyword:"const",params:{allowedValue: 28},message:"must be equal to constant"}];
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
validate23.errors = [{instancePath:instancePath+"/echarts_version",schemaPath:"#/properties/echarts_version/const",keyword:"const",params:{allowedValue: "6.1.0"},message:"must be equal to constant"}];
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
if("ranking-svg-ja-jp-node22-echarts6.v1" !== data.render_profile_id){
validate23.errors = [{instancePath:instancePath+"/render_profile_id",schemaPath:"#/properties/render_profile_id/const",keyword:"const",params:{allowedValue: "ranking-svg-ja-jp-node22-echarts6.v1"},message:"must be equal to constant"}];
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
else {
validate23.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate23.errors = vErrors;
return errors === 0;
}
validate23.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const chartSegmenter = new Intl.Segmenter("ja-JP", { granularity: "grapheme" });
const chartTitleSuffix = "のランキング";

function chartGraphemes(value) {
  return Array.from(chartSegmenter.segment(value), ({ segment }) => segment);
}

function chartGraphemeCount(value) {
  let count = 0;
  for (const _segment of chartSegmenter.segment(value)) count += 1;
  return count;
}

function chartGraphemeRange(value, minimum, maximum) {
  const count = chartGraphemeCount(value);
  return count >= minimum && count <= maximum;
}

function chartExpectedTitle(displayLabel) {
  const clusters = chartGraphemes(displayLabel);
  return clusters.length + chartGraphemeCount(chartTitleSuffix) <= 256
    ? displayLabel + chartTitleSuffix
    : clusters.slice(0, 249).join("") + "…" + chartTitleSuffix;
}

function chartSafeText(value) {
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
  if (!validateChartModelRaw(value)) return false;
  if (
    !chartGraphemeRange(value.title, 1, 256) ||
    !chartGraphemeRange(value.dimension.source_label, 1, 256) ||
    !chartGraphemeRange(value.dimension.display_label, 1, 256) ||
    (value.dimension.description !== null && !chartGraphemeRange(value.dimension.description, 0, 256)) ||
    (value.measure.column !== null && !chartGraphemeRange(value.measure.column, 1, 256)) ||
    value.title !== chartExpectedTitle(value.dimension.display_label)
  ) return false;
  const rows = value.rows;
  const analyzedRows = value.population.analyzed_rows;
  let countTotal = 0;
  let sawRemainder = false;
  for (let index = 0; index < rows.length; index += 1) {
    const row = rows[index];
    if (
      row.index !== index ||
      row.count > analyzedRows ||
      !chartGraphemeRange(row.display_label, 1, 256) ||
      (row.description !== null && !chartGraphemeRange(row.description, 0, 256))
    ) return false;
    countTotal += row.count;
    if (row.row_kind === "dimension_value") {
      if (row.semantic_label !== "データ中の分類値") return false;
    } else {
      if (
        sawRemainder ||
        index !== rows.length - 1 ||
        row.source_label !== "その他" ||
        row.semantic_label !== "上位表示外の合計"
      ) return false;
      sawRemainder = true;
    }
  }
  if (countTotal > analyzedRows) return false;
  if ((analyzedRows === 0) !== (rows.length === 0)) return false;
  const displayTexts = [
    value.title,
    value.dimension.source_label,
    value.dimension.display_label
  ];
  if (value.dimension.description !== null) displayTexts.push(value.dimension.description);
  if (value.measure.column !== null) displayTexts.push(value.measure.column);
  for (const row of rows) {
    displayTexts.push(row.source_label, row.display_label, row.semantic_label);
    if (row.description !== null) displayTexts.push(row.description);
  }
  displayTexts.push(...value.warnings);
  let displayGraphemes = 0;
  for (const text of displayTexts) {
    if (!chartSafeText(text)) return false;
    displayGraphemes += chartGraphemeCount(text);
    if (displayGraphemes > 20_000) return false;
  }
  return true;
}

export function validateRenderSpec(value) {
  if (!validateRenderSpecRaw(value)) return false;
  if (value.height === 675) return true;
  const rowCount = (value.height - 160) / 36;
  return Number.isInteger(rowCount) && rowCount >= 15 && rowCount <= 101;
}
