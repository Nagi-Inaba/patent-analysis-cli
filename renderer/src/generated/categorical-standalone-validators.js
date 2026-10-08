/* eslint-disable */
/* Generated validators enforce the closed categorical ChartModel contract. */
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
const schema32 = {"$id":"urn:patent-analysis:categorical-renderer-runtime:1.0.0","type":"object","additionalProperties":false,"required":["node_version","echarts_version","renderer_build_digest","render_profile_id"],"properties":{"node_version":{"const":"22.19.0"},"echarts_version":{"const":"6.1.0"},"renderer_build_digest":{"type":"string","pattern":"^[0-9a-f]{64}$"},"render_profile_id":{"const":"categorical-svg-ja-jp-node22-echarts6.v1"}}};

function validate21(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
/*# sourceURL="urn:patent-analysis:categorical-renderer-runtime:1.0.0" */;
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
if("categorical-svg-ja-jp-node22-echarts6.v1" !== data.render_profile_id){
validate21.errors = [{instancePath:instancePath+"/render_profile_id",schemaPath:"#/properties/render_profile_id/const",keyword:"const",params:{allowedValue: "categorical-svg-ja-jp-node22-echarts6.v1"},message:"must be equal to constant"}];
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

const validateCategoricalChartModelRaw = validate22;
const schema33 = {"$id":"urn:patent-analysis:categorical-chart-model:1.0.0","title":"Categorical ChartModel 1.0.0","oneOf":[{"$ref":"#/$defs/seriesModel"},{"$ref":"#/$defs/compositionModel"}],"$defs":{"measure":{"type":"object","required":["mode","role"],"additionalProperties":false,"properties":{"mode":{"enum":["count","sum","average","max","min"]},"role":{"type":["string","null"],"maxLength":64}}},"population":{"type":"object","required":["input_rows","analyzed_rows","excluded_rows"],"additionalProperties":false,"properties":{"input_rows":{"type":"integer","minimum":0},"analyzed_rows":{"type":"integer","minimum":0},"excluded_rows":{"type":"integer","minimum":0}}},"seriesItem":{"type":"object","required":["label","values","row_counts","is_other"],"additionalProperties":false,"properties":{"label":{"type":"string","minLength":1,"maxLength":4096},"values":{"type":"array","maxItems":400,"items":{"type":"number"}},"row_counts":{"type":"array","maxItems":400,"items":{"type":"integer","minimum":0}},"is_other":{"type":"boolean"}}},"compositionItem":{"type":"object","required":["label","value","row_count","share","share_basis","is_other"],"additionalProperties":false,"properties":{"label":{"type":"string","minLength":1,"maxLength":4096},"value":{"type":"number"},"row_count":{"type":"integer","minimum":0},"share":{"type":"number","minimum":0,"maximum":1},"share_basis":{"enum":["value","row_count"]},"is_other":{"type":"boolean"}}},"seriesModel":{"type":"object","required":["chart_model_contract_version","chart_type","mark","analysis_result_sha256","title","measure","x","series","population","warnings"],"additionalProperties":false,"properties":{"chart_model_contract_version":{"const":"1.0.0"},"chart_type":{"enum":["series.line","series.stacked-bar"]},"mark":{"enum":["series-line-svg.v1","series-stacked-bar-svg.v1"]},"analysis_result_sha256":{"type":"string","pattern":"^[0-9a-f]{64}$"},"title":{"type":"string","minLength":1,"maxLength":256},"measure":{"$ref":"#/$defs/measure"},"x":{"type":"array","maxItems":400,"items":{"type":"string","minLength":1,"maxLength":128}},"series":{"type":"array","maxItems":101,"items":{"$ref":"#/$defs/seriesItem"}},"population":{"$ref":"#/$defs/population"},"warnings":{"type":"array","maxItems":100,"items":{"type":"string","maxLength":4096}}},"allOf":[{"oneOf":[{"required":["chart_type","mark"],"properties":{"chart_type":{"const":"series.line"},"mark":{"const":"series-line-svg.v1"}}},{"required":["chart_type","mark"],"properties":{"chart_type":{"const":"series.stacked-bar"},"mark":{"const":"series-stacked-bar-svg.v1"}}}]}]},"compositionModel":{"type":"object","required":["chart_model_contract_version","chart_type","mark","analysis_result_sha256","title","measure","items","population","warnings"],"additionalProperties":false,"properties":{"chart_model_contract_version":{"const":"1.0.0"},"chart_type":{"enum":["composition.bar","composition.pie"]},"mark":{"enum":["composition-bar-svg.v1","composition-pie-svg.v1"]},"analysis_result_sha256":{"type":"string","pattern":"^[0-9a-f]{64}$"},"title":{"type":"string","minLength":1,"maxLength":256},"measure":{"$ref":"#/$defs/measure"},"items":{"type":"array","maxItems":101,"items":{"$ref":"#/$defs/compositionItem"}},"population":{"$ref":"#/$defs/population"},"warnings":{"type":"array","maxItems":100,"items":{"type":"string","maxLength":4096}}},"allOf":[{"oneOf":[{"required":["chart_type","mark"],"properties":{"chart_type":{"const":"composition.bar"},"mark":{"const":"composition-bar-svg.v1"}}},{"required":["chart_type","mark"],"properties":{"chart_type":{"const":"composition.pie"},"mark":{"const":"composition-pie-svg.v1"}}}]}]}}};
const schema34 = {"type":"object","required":["chart_model_contract_version","chart_type","mark","analysis_result_sha256","title","measure","x","series","population","warnings"],"additionalProperties":false,"properties":{"chart_model_contract_version":{"const":"1.0.0"},"chart_type":{"enum":["series.line","series.stacked-bar"]},"mark":{"enum":["series-line-svg.v1","series-stacked-bar-svg.v1"]},"analysis_result_sha256":{"type":"string","pattern":"^[0-9a-f]{64}$"},"title":{"type":"string","minLength":1,"maxLength":256},"measure":{"$ref":"#/$defs/measure"},"x":{"type":"array","maxItems":400,"items":{"type":"string","minLength":1,"maxLength":128}},"series":{"type":"array","maxItems":101,"items":{"$ref":"#/$defs/seriesItem"}},"population":{"$ref":"#/$defs/population"},"warnings":{"type":"array","maxItems":100,"items":{"type":"string","maxLength":4096}}},"allOf":[{"oneOf":[{"required":["chart_type","mark"],"properties":{"chart_type":{"const":"series.line"},"mark":{"const":"series-line-svg.v1"}}},{"required":["chart_type","mark"],"properties":{"chart_type":{"const":"series.stacked-bar"},"mark":{"const":"series-stacked-bar-svg.v1"}}}]}]};
const schema35 = {"type":"object","required":["mode","role"],"additionalProperties":false,"properties":{"mode":{"enum":["count","sum","average","max","min"]},"role":{"type":["string","null"],"maxLength":64}}};
const schema36 = {"type":"object","required":["label","values","row_counts","is_other"],"additionalProperties":false,"properties":{"label":{"type":"string","minLength":1,"maxLength":4096},"values":{"type":"array","maxItems":400,"items":{"type":"number"}},"row_counts":{"type":"array","maxItems":400,"items":{"type":"integer","minimum":0}},"is_other":{"type":"boolean"}}};
const schema37 = {"type":"object","required":["input_rows","analyzed_rows","excluded_rows"],"additionalProperties":false,"properties":{"input_rows":{"type":"integer","minimum":0},"analyzed_rows":{"type":"integer","minimum":0},"excluded_rows":{"type":"integer","minimum":0}}};
const func5 = Object.prototype.hasOwnProperty;

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
const _errs2 = errors;
let valid1 = false;
let passing0 = null;
const _errs3 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.chart_type === undefined) && (missing0 = "chart_type")) || ((data.mark === undefined) && (missing0 = "mark"))){
const err0 = {instancePath,schemaPath:"#/allOf/0/oneOf/0/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
else {
if(data.chart_type !== undefined){
const _errs4 = errors;
if("series.line" !== data.chart_type){
const err1 = {instancePath:instancePath+"/chart_type",schemaPath:"#/allOf/0/oneOf/0/properties/chart_type/const",keyword:"const",params:{allowedValue: "series.line"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
var valid2 = _errs4 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data.mark !== undefined){
const _errs5 = errors;
if("series-line-svg.v1" !== data.mark){
const err2 = {instancePath:instancePath+"/mark",schemaPath:"#/allOf/0/oneOf/0/properties/mark/const",keyword:"const",params:{allowedValue: "series-line-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
var valid2 = _errs5 === errors;
}
else {
var valid2 = true;
}
}
}
}
var _valid0 = _errs3 === errors;
if(_valid0){
valid1 = true;
passing0 = 0;
var props0 = {};
props0.chart_type = true;
props0.mark = true;
}
const _errs6 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
let missing1;
if(((data.chart_type === undefined) && (missing1 = "chart_type")) || ((data.mark === undefined) && (missing1 = "mark"))){
const err3 = {instancePath,schemaPath:"#/allOf/0/oneOf/1/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
else {
if(data.chart_type !== undefined){
const _errs7 = errors;
if("series.stacked-bar" !== data.chart_type){
const err4 = {instancePath:instancePath+"/chart_type",schemaPath:"#/allOf/0/oneOf/1/properties/chart_type/const",keyword:"const",params:{allowedValue: "series.stacked-bar"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
var valid3 = _errs7 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data.mark !== undefined){
const _errs8 = errors;
if("series-stacked-bar-svg.v1" !== data.mark){
const err5 = {instancePath:instancePath+"/mark",schemaPath:"#/allOf/0/oneOf/1/properties/mark/const",keyword:"const",params:{allowedValue: "series-stacked-bar-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
var valid3 = _errs8 === errors;
}
else {
var valid3 = true;
}
}
}
}
var _valid0 = _errs6 === errors;
if(_valid0 && valid1){
valid1 = false;
passing0 = [passing0, 1];
}
else {
if(_valid0){
valid1 = true;
passing0 = 1;
if(props0 !== true){
props0 = props0 || {};
props0.chart_type = true;
props0.mark = true;
}
}
}
if(!valid1){
const err6 = {instancePath,schemaPath:"#/allOf/0/oneOf",keyword:"oneOf",params:{passingSchemas: passing0},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
validate23.errors = vErrors;
return false;
}
else {
errors = _errs2;
if(vErrors !== null){
if(_errs2){
vErrors.length = _errs2;
}
else {
vErrors = null;
}
}
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing2;
if(((((((((((data.chart_model_contract_version === undefined) && (missing2 = "chart_model_contract_version")) || ((data.chart_type === undefined) && (missing2 = "chart_type"))) || ((data.mark === undefined) && (missing2 = "mark"))) || ((data.analysis_result_sha256 === undefined) && (missing2 = "analysis_result_sha256"))) || ((data.title === undefined) && (missing2 = "title"))) || ((data.measure === undefined) && (missing2 = "measure"))) || ((data.x === undefined) && (missing2 = "x"))) || ((data.series === undefined) && (missing2 = "series"))) || ((data.population === undefined) && (missing2 = "population"))) || ((data.warnings === undefined) && (missing2 = "warnings"))){
validate23.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
const _errs9 = errors;
for(const key0 in data){
if(!(func5.call(schema34.properties, key0))){
validate23.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs9 === errors){
if(data.chart_model_contract_version !== undefined){
const _errs10 = errors;
if("1.0.0" !== data.chart_model_contract_version){
validate23.errors = [{instancePath:instancePath+"/chart_model_contract_version",schemaPath:"#/properties/chart_model_contract_version/const",keyword:"const",params:{allowedValue: "1.0.0"},message:"must be equal to constant"}];
return false;
}
var valid4 = _errs10 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.chart_type !== undefined){
let data5 = data.chart_type;
const _errs11 = errors;
if(!((data5 === "series.line") || (data5 === "series.stacked-bar"))){
validate23.errors = [{instancePath:instancePath+"/chart_type",schemaPath:"#/properties/chart_type/enum",keyword:"enum",params:{allowedValues: schema34.properties.chart_type.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid4 = _errs11 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.mark !== undefined){
let data6 = data.mark;
const _errs12 = errors;
if(!((data6 === "series-line-svg.v1") || (data6 === "series-stacked-bar-svg.v1"))){
validate23.errors = [{instancePath:instancePath+"/mark",schemaPath:"#/properties/mark/enum",keyword:"enum",params:{allowedValues: schema34.properties.mark.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid4 = _errs12 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.analysis_result_sha256 !== undefined){
let data7 = data.analysis_result_sha256;
const _errs13 = errors;
if(errors === _errs13){
if(typeof data7 === "string"){
if(!pattern5.test(data7)){
validate23.errors = [{instancePath:instancePath+"/analysis_result_sha256",schemaPath:"#/properties/analysis_result_sha256/pattern",keyword:"pattern",params:{pattern: "^[0-9a-f]{64}$"},message:"must match pattern \""+"^[0-9a-f]{64}$"+"\""}];
return false;
}
}
else {
validate23.errors = [{instancePath:instancePath+"/analysis_result_sha256",schemaPath:"#/properties/analysis_result_sha256/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid4 = _errs13 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.title !== undefined){
let data8 = data.title;
const _errs15 = errors;
if(errors === _errs15){
if(typeof data8 === "string"){
if(func1(data8) > 256){
validate23.errors = [{instancePath:instancePath+"/title",schemaPath:"#/properties/title/maxLength",keyword:"maxLength",params:{limit: 256},message:"must NOT have more than 256 characters"}];
return false;
}
else {
if(func1(data8) < 1){
validate23.errors = [{instancePath:instancePath+"/title",schemaPath:"#/properties/title/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/title",schemaPath:"#/properties/title/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid4 = _errs15 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.measure !== undefined){
let data9 = data.measure;
const _errs17 = errors;
const _errs18 = errors;
if(errors === _errs18){
if(data9 && typeof data9 == "object" && !Array.isArray(data9)){
let missing3;
if(((data9.mode === undefined) && (missing3 = "mode")) || ((data9.role === undefined) && (missing3 = "role"))){
validate23.errors = [{instancePath:instancePath+"/measure",schemaPath:"#/$defs/measure/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"}];
return false;
}
else {
const _errs20 = errors;
for(const key1 in data9){
if(!((key1 === "mode") || (key1 === "role"))){
validate23.errors = [{instancePath:instancePath+"/measure",schemaPath:"#/$defs/measure/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs20 === errors){
if(data9.mode !== undefined){
let data10 = data9.mode;
const _errs21 = errors;
if(!(((((data10 === "count") || (data10 === "sum")) || (data10 === "average")) || (data10 === "max")) || (data10 === "min"))){
validate23.errors = [{instancePath:instancePath+"/measure/mode",schemaPath:"#/$defs/measure/properties/mode/enum",keyword:"enum",params:{allowedValues: schema35.properties.mode.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid6 = _errs21 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data9.role !== undefined){
let data11 = data9.role;
const _errs22 = errors;
if((typeof data11 !== "string") && (data11 !== null)){
validate23.errors = [{instancePath:instancePath+"/measure/role",schemaPath:"#/$defs/measure/properties/role/type",keyword:"type",params:{type: schema35.properties.role.type},message:"must be string,null"}];
return false;
}
if(errors === _errs22){
if(typeof data11 === "string"){
if(func1(data11) > 64){
validate23.errors = [{instancePath:instancePath+"/measure/role",schemaPath:"#/$defs/measure/properties/role/maxLength",keyword:"maxLength",params:{limit: 64},message:"must NOT have more than 64 characters"}];
return false;
}
}
}
var valid6 = _errs22 === errors;
}
else {
var valid6 = true;
}
}
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/measure",schemaPath:"#/$defs/measure/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid4 = _errs17 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.x !== undefined){
let data12 = data.x;
const _errs24 = errors;
if(errors === _errs24){
if(Array.isArray(data12)){
if(data12.length > 400){
validate23.errors = [{instancePath:instancePath+"/x",schemaPath:"#/properties/x/maxItems",keyword:"maxItems",params:{limit: 400},message:"must NOT have more than 400 items"}];
return false;
}
else {
var valid7 = true;
const len0 = data12.length;
for(let i0=0; i0<len0; i0++){
let data13 = data12[i0];
const _errs26 = errors;
if(errors === _errs26){
if(typeof data13 === "string"){
if(func1(data13) > 128){
validate23.errors = [{instancePath:instancePath+"/x/" + i0,schemaPath:"#/properties/x/items/maxLength",keyword:"maxLength",params:{limit: 128},message:"must NOT have more than 128 characters"}];
return false;
}
else {
if(func1(data13) < 1){
validate23.errors = [{instancePath:instancePath+"/x/" + i0,schemaPath:"#/properties/x/items/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/x/" + i0,schemaPath:"#/properties/x/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid7 = _errs26 === errors;
if(!valid7){
break;
}
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/x",schemaPath:"#/properties/x/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid4 = _errs24 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.series !== undefined){
let data14 = data.series;
const _errs28 = errors;
if(errors === _errs28){
if(Array.isArray(data14)){
if(data14.length > 101){
validate23.errors = [{instancePath:instancePath+"/series",schemaPath:"#/properties/series/maxItems",keyword:"maxItems",params:{limit: 101},message:"must NOT have more than 101 items"}];
return false;
}
else {
var valid8 = true;
const len1 = data14.length;
for(let i1=0; i1<len1; i1++){
let data15 = data14[i1];
const _errs30 = errors;
const _errs31 = errors;
if(errors === _errs31){
if(data15 && typeof data15 == "object" && !Array.isArray(data15)){
let missing4;
if(((((data15.label === undefined) && (missing4 = "label")) || ((data15.values === undefined) && (missing4 = "values"))) || ((data15.row_counts === undefined) && (missing4 = "row_counts"))) || ((data15.is_other === undefined) && (missing4 = "is_other"))){
validate23.errors = [{instancePath:instancePath+"/series/" + i1,schemaPath:"#/$defs/seriesItem/required",keyword:"required",params:{missingProperty: missing4},message:"must have required property '"+missing4+"'"}];
return false;
}
else {
const _errs33 = errors;
for(const key2 in data15){
if(!((((key2 === "label") || (key2 === "values")) || (key2 === "row_counts")) || (key2 === "is_other"))){
validate23.errors = [{instancePath:instancePath+"/series/" + i1,schemaPath:"#/$defs/seriesItem/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key2},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs33 === errors){
if(data15.label !== undefined){
let data16 = data15.label;
const _errs34 = errors;
if(errors === _errs34){
if(typeof data16 === "string"){
if(func1(data16) > 4096){
validate23.errors = [{instancePath:instancePath+"/series/" + i1+"/label",schemaPath:"#/$defs/seriesItem/properties/label/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data16) < 1){
validate23.errors = [{instancePath:instancePath+"/series/" + i1+"/label",schemaPath:"#/$defs/seriesItem/properties/label/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/series/" + i1+"/label",schemaPath:"#/$defs/seriesItem/properties/label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid10 = _errs34 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.values !== undefined){
let data17 = data15.values;
const _errs36 = errors;
if(errors === _errs36){
if(Array.isArray(data17)){
if(data17.length > 400){
validate23.errors = [{instancePath:instancePath+"/series/" + i1+"/values",schemaPath:"#/$defs/seriesItem/properties/values/maxItems",keyword:"maxItems",params:{limit: 400},message:"must NOT have more than 400 items"}];
return false;
}
else {
var valid11 = true;
const len2 = data17.length;
for(let i2=0; i2<len2; i2++){
let data18 = data17[i2];
const _errs38 = errors;
if(!((typeof data18 == "number") && (isFinite(data18)))){
validate23.errors = [{instancePath:instancePath+"/series/" + i1+"/values/" + i2,schemaPath:"#/$defs/seriesItem/properties/values/items/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
var valid11 = _errs38 === errors;
if(!valid11){
break;
}
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/series/" + i1+"/values",schemaPath:"#/$defs/seriesItem/properties/values/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid10 = _errs36 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.row_counts !== undefined){
let data19 = data15.row_counts;
const _errs40 = errors;
if(errors === _errs40){
if(Array.isArray(data19)){
if(data19.length > 400){
validate23.errors = [{instancePath:instancePath+"/series/" + i1+"/row_counts",schemaPath:"#/$defs/seriesItem/properties/row_counts/maxItems",keyword:"maxItems",params:{limit: 400},message:"must NOT have more than 400 items"}];
return false;
}
else {
var valid12 = true;
const len3 = data19.length;
for(let i3=0; i3<len3; i3++){
let data20 = data19[i3];
const _errs42 = errors;
if(!(((typeof data20 == "number") && (!(data20 % 1) && !isNaN(data20))) && (isFinite(data20)))){
validate23.errors = [{instancePath:instancePath+"/series/" + i1+"/row_counts/" + i3,schemaPath:"#/$defs/seriesItem/properties/row_counts/items/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs42){
if((typeof data20 == "number") && (isFinite(data20))){
if(data20 < 0 || isNaN(data20)){
validate23.errors = [{instancePath:instancePath+"/series/" + i1+"/row_counts/" + i3,schemaPath:"#/$defs/seriesItem/properties/row_counts/items/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid12 = _errs42 === errors;
if(!valid12){
break;
}
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/series/" + i1+"/row_counts",schemaPath:"#/$defs/seriesItem/properties/row_counts/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid10 = _errs40 === errors;
}
else {
var valid10 = true;
}
if(valid10){
if(data15.is_other !== undefined){
const _errs44 = errors;
if(typeof data15.is_other !== "boolean"){
validate23.errors = [{instancePath:instancePath+"/series/" + i1+"/is_other",schemaPath:"#/$defs/seriesItem/properties/is_other/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid10 = _errs44 === errors;
}
else {
var valid10 = true;
}
}
}
}
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/series/" + i1,schemaPath:"#/$defs/seriesItem/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid8 = _errs30 === errors;
if(!valid8){
break;
}
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/series",schemaPath:"#/properties/series/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid4 = _errs28 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.population !== undefined){
let data22 = data.population;
const _errs46 = errors;
const _errs47 = errors;
if(errors === _errs47){
if(data22 && typeof data22 == "object" && !Array.isArray(data22)){
let missing5;
if((((data22.input_rows === undefined) && (missing5 = "input_rows")) || ((data22.analyzed_rows === undefined) && (missing5 = "analyzed_rows"))) || ((data22.excluded_rows === undefined) && (missing5 = "excluded_rows"))){
validate23.errors = [{instancePath:instancePath+"/population",schemaPath:"#/$defs/population/required",keyword:"required",params:{missingProperty: missing5},message:"must have required property '"+missing5+"'"}];
return false;
}
else {
const _errs49 = errors;
for(const key3 in data22){
if(!(((key3 === "input_rows") || (key3 === "analyzed_rows")) || (key3 === "excluded_rows"))){
validate23.errors = [{instancePath:instancePath+"/population",schemaPath:"#/$defs/population/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key3},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs49 === errors){
if(data22.input_rows !== undefined){
let data23 = data22.input_rows;
const _errs50 = errors;
if(!(((typeof data23 == "number") && (!(data23 % 1) && !isNaN(data23))) && (isFinite(data23)))){
validate23.errors = [{instancePath:instancePath+"/population/input_rows",schemaPath:"#/$defs/population/properties/input_rows/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs50){
if((typeof data23 == "number") && (isFinite(data23))){
if(data23 < 0 || isNaN(data23)){
validate23.errors = [{instancePath:instancePath+"/population/input_rows",schemaPath:"#/$defs/population/properties/input_rows/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid14 = _errs50 === errors;
}
else {
var valid14 = true;
}
if(valid14){
if(data22.analyzed_rows !== undefined){
let data24 = data22.analyzed_rows;
const _errs52 = errors;
if(!(((typeof data24 == "number") && (!(data24 % 1) && !isNaN(data24))) && (isFinite(data24)))){
validate23.errors = [{instancePath:instancePath+"/population/analyzed_rows",schemaPath:"#/$defs/population/properties/analyzed_rows/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs52){
if((typeof data24 == "number") && (isFinite(data24))){
if(data24 < 0 || isNaN(data24)){
validate23.errors = [{instancePath:instancePath+"/population/analyzed_rows",schemaPath:"#/$defs/population/properties/analyzed_rows/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid14 = _errs52 === errors;
}
else {
var valid14 = true;
}
if(valid14){
if(data22.excluded_rows !== undefined){
let data25 = data22.excluded_rows;
const _errs54 = errors;
if(!(((typeof data25 == "number") && (!(data25 % 1) && !isNaN(data25))) && (isFinite(data25)))){
validate23.errors = [{instancePath:instancePath+"/population/excluded_rows",schemaPath:"#/$defs/population/properties/excluded_rows/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs54){
if((typeof data25 == "number") && (isFinite(data25))){
if(data25 < 0 || isNaN(data25)){
validate23.errors = [{instancePath:instancePath+"/population/excluded_rows",schemaPath:"#/$defs/population/properties/excluded_rows/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid14 = _errs54 === errors;
}
else {
var valid14 = true;
}
}
}
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/population",schemaPath:"#/$defs/population/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid4 = _errs46 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.warnings !== undefined){
let data26 = data.warnings;
const _errs56 = errors;
if(errors === _errs56){
if(Array.isArray(data26)){
if(data26.length > 100){
validate23.errors = [{instancePath:instancePath+"/warnings",schemaPath:"#/properties/warnings/maxItems",keyword:"maxItems",params:{limit: 100},message:"must NOT have more than 100 items"}];
return false;
}
else {
var valid15 = true;
const len4 = data26.length;
for(let i4=0; i4<len4; i4++){
let data27 = data26[i4];
const _errs58 = errors;
if(errors === _errs58){
if(typeof data27 === "string"){
if(func1(data27) > 4096){
validate23.errors = [{instancePath:instancePath+"/warnings/" + i4,schemaPath:"#/properties/warnings/items/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
}
else {
validate23.errors = [{instancePath:instancePath+"/warnings/" + i4,schemaPath:"#/properties/warnings/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid15 = _errs58 === errors;
if(!valid15){
break;
}
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/warnings",schemaPath:"#/properties/warnings/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid4 = _errs56 === errors;
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

const schema38 = {"type":"object","required":["chart_model_contract_version","chart_type","mark","analysis_result_sha256","title","measure","items","population","warnings"],"additionalProperties":false,"properties":{"chart_model_contract_version":{"const":"1.0.0"},"chart_type":{"enum":["composition.bar","composition.pie"]},"mark":{"enum":["composition-bar-svg.v1","composition-pie-svg.v1"]},"analysis_result_sha256":{"type":"string","pattern":"^[0-9a-f]{64}$"},"title":{"type":"string","minLength":1,"maxLength":256},"measure":{"$ref":"#/$defs/measure"},"items":{"type":"array","maxItems":101,"items":{"$ref":"#/$defs/compositionItem"}},"population":{"$ref":"#/$defs/population"},"warnings":{"type":"array","maxItems":100,"items":{"type":"string","maxLength":4096}}},"allOf":[{"oneOf":[{"required":["chart_type","mark"],"properties":{"chart_type":{"const":"composition.bar"},"mark":{"const":"composition-bar-svg.v1"}}},{"required":["chart_type","mark"],"properties":{"chart_type":{"const":"composition.pie"},"mark":{"const":"composition-pie-svg.v1"}}}]}]};
const schema40 = {"type":"object","required":["label","value","row_count","share","share_basis","is_other"],"additionalProperties":false,"properties":{"label":{"type":"string","minLength":1,"maxLength":4096},"value":{"type":"number"},"row_count":{"type":"integer","minimum":0},"share":{"type":"number","minimum":0,"maximum":1},"share_basis":{"enum":["value","row_count"]},"is_other":{"type":"boolean"}}};

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
const _errs2 = errors;
let valid1 = false;
let passing0 = null;
const _errs3 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
let missing0;
if(((data.chart_type === undefined) && (missing0 = "chart_type")) || ((data.mark === undefined) && (missing0 = "mark"))){
const err0 = {instancePath,schemaPath:"#/allOf/0/oneOf/0/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
}
else {
if(data.chart_type !== undefined){
const _errs4 = errors;
if("composition.bar" !== data.chart_type){
const err1 = {instancePath:instancePath+"/chart_type",schemaPath:"#/allOf/0/oneOf/0/properties/chart_type/const",keyword:"const",params:{allowedValue: "composition.bar"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err1];
}
else {
vErrors.push(err1);
}
errors++;
}
var valid2 = _errs4 === errors;
}
else {
var valid2 = true;
}
if(valid2){
if(data.mark !== undefined){
const _errs5 = errors;
if("composition-bar-svg.v1" !== data.mark){
const err2 = {instancePath:instancePath+"/mark",schemaPath:"#/allOf/0/oneOf/0/properties/mark/const",keyword:"const",params:{allowedValue: "composition-bar-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err2];
}
else {
vErrors.push(err2);
}
errors++;
}
var valid2 = _errs5 === errors;
}
else {
var valid2 = true;
}
}
}
}
var _valid0 = _errs3 === errors;
if(_valid0){
valid1 = true;
passing0 = 0;
var props0 = {};
props0.chart_type = true;
props0.mark = true;
}
const _errs6 = errors;
if(data && typeof data == "object" && !Array.isArray(data)){
let missing1;
if(((data.chart_type === undefined) && (missing1 = "chart_type")) || ((data.mark === undefined) && (missing1 = "mark"))){
const err3 = {instancePath,schemaPath:"#/allOf/0/oneOf/1/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"};
if(vErrors === null){
vErrors = [err3];
}
else {
vErrors.push(err3);
}
errors++;
}
else {
if(data.chart_type !== undefined){
const _errs7 = errors;
if("composition.pie" !== data.chart_type){
const err4 = {instancePath:instancePath+"/chart_type",schemaPath:"#/allOf/0/oneOf/1/properties/chart_type/const",keyword:"const",params:{allowedValue: "composition.pie"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err4];
}
else {
vErrors.push(err4);
}
errors++;
}
var valid3 = _errs7 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data.mark !== undefined){
const _errs8 = errors;
if("composition-pie-svg.v1" !== data.mark){
const err5 = {instancePath:instancePath+"/mark",schemaPath:"#/allOf/0/oneOf/1/properties/mark/const",keyword:"const",params:{allowedValue: "composition-pie-svg.v1"},message:"must be equal to constant"};
if(vErrors === null){
vErrors = [err5];
}
else {
vErrors.push(err5);
}
errors++;
}
var valid3 = _errs8 === errors;
}
else {
var valid3 = true;
}
}
}
}
var _valid0 = _errs6 === errors;
if(_valid0 && valid1){
valid1 = false;
passing0 = [passing0, 1];
}
else {
if(_valid0){
valid1 = true;
passing0 = 1;
if(props0 !== true){
props0 = props0 || {};
props0.chart_type = true;
props0.mark = true;
}
}
}
if(!valid1){
const err6 = {instancePath,schemaPath:"#/allOf/0/oneOf",keyword:"oneOf",params:{passingSchemas: passing0},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err6];
}
else {
vErrors.push(err6);
}
errors++;
validate25.errors = vErrors;
return false;
}
else {
errors = _errs2;
if(vErrors !== null){
if(_errs2){
vErrors.length = _errs2;
}
else {
vErrors = null;
}
}
}
if(errors === 0){
if(data && typeof data == "object" && !Array.isArray(data)){
let missing2;
if((((((((((data.chart_model_contract_version === undefined) && (missing2 = "chart_model_contract_version")) || ((data.chart_type === undefined) && (missing2 = "chart_type"))) || ((data.mark === undefined) && (missing2 = "mark"))) || ((data.analysis_result_sha256 === undefined) && (missing2 = "analysis_result_sha256"))) || ((data.title === undefined) && (missing2 = "title"))) || ((data.measure === undefined) && (missing2 = "measure"))) || ((data.items === undefined) && (missing2 = "items"))) || ((data.population === undefined) && (missing2 = "population"))) || ((data.warnings === undefined) && (missing2 = "warnings"))){
validate25.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
const _errs9 = errors;
for(const key0 in data){
if(!(func5.call(schema38.properties, key0))){
validate25.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs9 === errors){
if(data.chart_model_contract_version !== undefined){
const _errs10 = errors;
if("1.0.0" !== data.chart_model_contract_version){
validate25.errors = [{instancePath:instancePath+"/chart_model_contract_version",schemaPath:"#/properties/chart_model_contract_version/const",keyword:"const",params:{allowedValue: "1.0.0"},message:"must be equal to constant"}];
return false;
}
var valid4 = _errs10 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.chart_type !== undefined){
let data5 = data.chart_type;
const _errs11 = errors;
if(!((data5 === "composition.bar") || (data5 === "composition.pie"))){
validate25.errors = [{instancePath:instancePath+"/chart_type",schemaPath:"#/properties/chart_type/enum",keyword:"enum",params:{allowedValues: schema38.properties.chart_type.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid4 = _errs11 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.mark !== undefined){
let data6 = data.mark;
const _errs12 = errors;
if(!((data6 === "composition-bar-svg.v1") || (data6 === "composition-pie-svg.v1"))){
validate25.errors = [{instancePath:instancePath+"/mark",schemaPath:"#/properties/mark/enum",keyword:"enum",params:{allowedValues: schema38.properties.mark.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid4 = _errs12 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.analysis_result_sha256 !== undefined){
let data7 = data.analysis_result_sha256;
const _errs13 = errors;
if(errors === _errs13){
if(typeof data7 === "string"){
if(!pattern5.test(data7)){
validate25.errors = [{instancePath:instancePath+"/analysis_result_sha256",schemaPath:"#/properties/analysis_result_sha256/pattern",keyword:"pattern",params:{pattern: "^[0-9a-f]{64}$"},message:"must match pattern \""+"^[0-9a-f]{64}$"+"\""}];
return false;
}
}
else {
validate25.errors = [{instancePath:instancePath+"/analysis_result_sha256",schemaPath:"#/properties/analysis_result_sha256/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid4 = _errs13 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.title !== undefined){
let data8 = data.title;
const _errs15 = errors;
if(errors === _errs15){
if(typeof data8 === "string"){
if(func1(data8) > 256){
validate25.errors = [{instancePath:instancePath+"/title",schemaPath:"#/properties/title/maxLength",keyword:"maxLength",params:{limit: 256},message:"must NOT have more than 256 characters"}];
return false;
}
else {
if(func1(data8) < 1){
validate25.errors = [{instancePath:instancePath+"/title",schemaPath:"#/properties/title/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate25.errors = [{instancePath:instancePath+"/title",schemaPath:"#/properties/title/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid4 = _errs15 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.measure !== undefined){
let data9 = data.measure;
const _errs17 = errors;
const _errs18 = errors;
if(errors === _errs18){
if(data9 && typeof data9 == "object" && !Array.isArray(data9)){
let missing3;
if(((data9.mode === undefined) && (missing3 = "mode")) || ((data9.role === undefined) && (missing3 = "role"))){
validate25.errors = [{instancePath:instancePath+"/measure",schemaPath:"#/$defs/measure/required",keyword:"required",params:{missingProperty: missing3},message:"must have required property '"+missing3+"'"}];
return false;
}
else {
const _errs20 = errors;
for(const key1 in data9){
if(!((key1 === "mode") || (key1 === "role"))){
validate25.errors = [{instancePath:instancePath+"/measure",schemaPath:"#/$defs/measure/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs20 === errors){
if(data9.mode !== undefined){
let data10 = data9.mode;
const _errs21 = errors;
if(!(((((data10 === "count") || (data10 === "sum")) || (data10 === "average")) || (data10 === "max")) || (data10 === "min"))){
validate25.errors = [{instancePath:instancePath+"/measure/mode",schemaPath:"#/$defs/measure/properties/mode/enum",keyword:"enum",params:{allowedValues: schema35.properties.mode.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid6 = _errs21 === errors;
}
else {
var valid6 = true;
}
if(valid6){
if(data9.role !== undefined){
let data11 = data9.role;
const _errs22 = errors;
if((typeof data11 !== "string") && (data11 !== null)){
validate25.errors = [{instancePath:instancePath+"/measure/role",schemaPath:"#/$defs/measure/properties/role/type",keyword:"type",params:{type: schema35.properties.role.type},message:"must be string,null"}];
return false;
}
if(errors === _errs22){
if(typeof data11 === "string"){
if(func1(data11) > 64){
validate25.errors = [{instancePath:instancePath+"/measure/role",schemaPath:"#/$defs/measure/properties/role/maxLength",keyword:"maxLength",params:{limit: 64},message:"must NOT have more than 64 characters"}];
return false;
}
}
}
var valid6 = _errs22 === errors;
}
else {
var valid6 = true;
}
}
}
}
}
else {
validate25.errors = [{instancePath:instancePath+"/measure",schemaPath:"#/$defs/measure/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid4 = _errs17 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.items !== undefined){
let data12 = data.items;
const _errs24 = errors;
if(errors === _errs24){
if(Array.isArray(data12)){
if(data12.length > 101){
validate25.errors = [{instancePath:instancePath+"/items",schemaPath:"#/properties/items/maxItems",keyword:"maxItems",params:{limit: 101},message:"must NOT have more than 101 items"}];
return false;
}
else {
var valid7 = true;
const len0 = data12.length;
for(let i0=0; i0<len0; i0++){
let data13 = data12[i0];
const _errs26 = errors;
const _errs27 = errors;
if(errors === _errs27){
if(data13 && typeof data13 == "object" && !Array.isArray(data13)){
let missing4;
if(((((((data13.label === undefined) && (missing4 = "label")) || ((data13.value === undefined) && (missing4 = "value"))) || ((data13.row_count === undefined) && (missing4 = "row_count"))) || ((data13.share === undefined) && (missing4 = "share"))) || ((data13.share_basis === undefined) && (missing4 = "share_basis"))) || ((data13.is_other === undefined) && (missing4 = "is_other"))){
validate25.errors = [{instancePath:instancePath+"/items/" + i0,schemaPath:"#/$defs/compositionItem/required",keyword:"required",params:{missingProperty: missing4},message:"must have required property '"+missing4+"'"}];
return false;
}
else {
const _errs29 = errors;
for(const key2 in data13){
if(!((((((key2 === "label") || (key2 === "value")) || (key2 === "row_count")) || (key2 === "share")) || (key2 === "share_basis")) || (key2 === "is_other"))){
validate25.errors = [{instancePath:instancePath+"/items/" + i0,schemaPath:"#/$defs/compositionItem/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key2},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs29 === errors){
if(data13.label !== undefined){
let data14 = data13.label;
const _errs30 = errors;
if(errors === _errs30){
if(typeof data14 === "string"){
if(func1(data14) > 4096){
validate25.errors = [{instancePath:instancePath+"/items/" + i0+"/label",schemaPath:"#/$defs/compositionItem/properties/label/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
else {
if(func1(data14) < 1){
validate25.errors = [{instancePath:instancePath+"/items/" + i0+"/label",schemaPath:"#/$defs/compositionItem/properties/label/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate25.errors = [{instancePath:instancePath+"/items/" + i0+"/label",schemaPath:"#/$defs/compositionItem/properties/label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid9 = _errs30 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data13.value !== undefined){
let data15 = data13.value;
const _errs32 = errors;
if(!((typeof data15 == "number") && (isFinite(data15)))){
validate25.errors = [{instancePath:instancePath+"/items/" + i0+"/value",schemaPath:"#/$defs/compositionItem/properties/value/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
var valid9 = _errs32 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data13.row_count !== undefined){
let data16 = data13.row_count;
const _errs34 = errors;
if(!(((typeof data16 == "number") && (!(data16 % 1) && !isNaN(data16))) && (isFinite(data16)))){
validate25.errors = [{instancePath:instancePath+"/items/" + i0+"/row_count",schemaPath:"#/$defs/compositionItem/properties/row_count/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs34){
if((typeof data16 == "number") && (isFinite(data16))){
if(data16 < 0 || isNaN(data16)){
validate25.errors = [{instancePath:instancePath+"/items/" + i0+"/row_count",schemaPath:"#/$defs/compositionItem/properties/row_count/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid9 = _errs34 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data13.share !== undefined){
let data17 = data13.share;
const _errs36 = errors;
if(errors === _errs36){
if((typeof data17 == "number") && (isFinite(data17))){
if(data17 > 1 || isNaN(data17)){
validate25.errors = [{instancePath:instancePath+"/items/" + i0+"/share",schemaPath:"#/$defs/compositionItem/properties/share/maximum",keyword:"maximum",params:{comparison: "<=", limit: 1},message:"must be <= 1"}];
return false;
}
else {
if(data17 < 0 || isNaN(data17)){
validate25.errors = [{instancePath:instancePath+"/items/" + i0+"/share",schemaPath:"#/$defs/compositionItem/properties/share/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
else {
validate25.errors = [{instancePath:instancePath+"/items/" + i0+"/share",schemaPath:"#/$defs/compositionItem/properties/share/type",keyword:"type",params:{type: "number"},message:"must be number"}];
return false;
}
}
var valid9 = _errs36 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data13.share_basis !== undefined){
let data18 = data13.share_basis;
const _errs38 = errors;
if(!((data18 === "value") || (data18 === "row_count"))){
validate25.errors = [{instancePath:instancePath+"/items/" + i0+"/share_basis",schemaPath:"#/$defs/compositionItem/properties/share_basis/enum",keyword:"enum",params:{allowedValues: schema40.properties.share_basis.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid9 = _errs38 === errors;
}
else {
var valid9 = true;
}
if(valid9){
if(data13.is_other !== undefined){
const _errs39 = errors;
if(typeof data13.is_other !== "boolean"){
validate25.errors = [{instancePath:instancePath+"/items/" + i0+"/is_other",schemaPath:"#/$defs/compositionItem/properties/is_other/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid9 = _errs39 === errors;
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
}
}
else {
validate25.errors = [{instancePath:instancePath+"/items/" + i0,schemaPath:"#/$defs/compositionItem/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid7 = _errs26 === errors;
if(!valid7){
break;
}
}
}
}
else {
validate25.errors = [{instancePath:instancePath+"/items",schemaPath:"#/properties/items/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid4 = _errs24 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.population !== undefined){
let data20 = data.population;
const _errs41 = errors;
const _errs42 = errors;
if(errors === _errs42){
if(data20 && typeof data20 == "object" && !Array.isArray(data20)){
let missing5;
if((((data20.input_rows === undefined) && (missing5 = "input_rows")) || ((data20.analyzed_rows === undefined) && (missing5 = "analyzed_rows"))) || ((data20.excluded_rows === undefined) && (missing5 = "excluded_rows"))){
validate25.errors = [{instancePath:instancePath+"/population",schemaPath:"#/$defs/population/required",keyword:"required",params:{missingProperty: missing5},message:"must have required property '"+missing5+"'"}];
return false;
}
else {
const _errs44 = errors;
for(const key3 in data20){
if(!(((key3 === "input_rows") || (key3 === "analyzed_rows")) || (key3 === "excluded_rows"))){
validate25.errors = [{instancePath:instancePath+"/population",schemaPath:"#/$defs/population/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key3},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs44 === errors){
if(data20.input_rows !== undefined){
let data21 = data20.input_rows;
const _errs45 = errors;
if(!(((typeof data21 == "number") && (!(data21 % 1) && !isNaN(data21))) && (isFinite(data21)))){
validate25.errors = [{instancePath:instancePath+"/population/input_rows",schemaPath:"#/$defs/population/properties/input_rows/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs45){
if((typeof data21 == "number") && (isFinite(data21))){
if(data21 < 0 || isNaN(data21)){
validate25.errors = [{instancePath:instancePath+"/population/input_rows",schemaPath:"#/$defs/population/properties/input_rows/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid11 = _errs45 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data20.analyzed_rows !== undefined){
let data22 = data20.analyzed_rows;
const _errs47 = errors;
if(!(((typeof data22 == "number") && (!(data22 % 1) && !isNaN(data22))) && (isFinite(data22)))){
validate25.errors = [{instancePath:instancePath+"/population/analyzed_rows",schemaPath:"#/$defs/population/properties/analyzed_rows/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs47){
if((typeof data22 == "number") && (isFinite(data22))){
if(data22 < 0 || isNaN(data22)){
validate25.errors = [{instancePath:instancePath+"/population/analyzed_rows",schemaPath:"#/$defs/population/properties/analyzed_rows/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid11 = _errs47 === errors;
}
else {
var valid11 = true;
}
if(valid11){
if(data20.excluded_rows !== undefined){
let data23 = data20.excluded_rows;
const _errs49 = errors;
if(!(((typeof data23 == "number") && (!(data23 % 1) && !isNaN(data23))) && (isFinite(data23)))){
validate25.errors = [{instancePath:instancePath+"/population/excluded_rows",schemaPath:"#/$defs/population/properties/excluded_rows/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs49){
if((typeof data23 == "number") && (isFinite(data23))){
if(data23 < 0 || isNaN(data23)){
validate25.errors = [{instancePath:instancePath+"/population/excluded_rows",schemaPath:"#/$defs/population/properties/excluded_rows/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid11 = _errs49 === errors;
}
else {
var valid11 = true;
}
}
}
}
}
}
else {
validate25.errors = [{instancePath:instancePath+"/population",schemaPath:"#/$defs/population/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid4 = _errs41 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data.warnings !== undefined){
let data24 = data.warnings;
const _errs51 = errors;
if(errors === _errs51){
if(Array.isArray(data24)){
if(data24.length > 100){
validate25.errors = [{instancePath:instancePath+"/warnings",schemaPath:"#/properties/warnings/maxItems",keyword:"maxItems",params:{limit: 100},message:"must NOT have more than 100 items"}];
return false;
}
else {
var valid12 = true;
const len1 = data24.length;
for(let i1=0; i1<len1; i1++){
let data25 = data24[i1];
const _errs53 = errors;
if(errors === _errs53){
if(typeof data25 === "string"){
if(func1(data25) > 4096){
validate25.errors = [{instancePath:instancePath+"/warnings/" + i1,schemaPath:"#/properties/warnings/items/maxLength",keyword:"maxLength",params:{limit: 4096},message:"must NOT have more than 4096 characters"}];
return false;
}
}
else {
validate25.errors = [{instancePath:instancePath+"/warnings/" + i1,schemaPath:"#/properties/warnings/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid12 = _errs53 === errors;
if(!valid12){
break;
}
}
}
}
else {
validate25.errors = [{instancePath:instancePath+"/warnings",schemaPath:"#/properties/warnings/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid4 = _errs51 === errors;
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


function validate22(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
/*# sourceURL="urn:patent-analysis:categorical-chart-model:1.0.0" */;
let vErrors = null;
let errors = 0;
const evaluated0 = validate22.evaluated;
if(evaluated0.dynamicProps){
evaluated0.props = undefined;
}
if(evaluated0.dynamicItems){
evaluated0.items = undefined;
}
const _errs0 = errors;
let valid0 = false;
let passing0 = null;
const _errs1 = errors;
if(!(validate23(data, {instancePath,parentData,parentDataProperty,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate23.errors : vErrors.concat(validate23.errors);
errors = vErrors.length;
}
var _valid0 = _errs1 === errors;
if(_valid0){
valid0 = true;
passing0 = 0;
var props0 = true;
}
const _errs2 = errors;
if(!(validate25(data, {instancePath,parentData,parentDataProperty,rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate25.errors : vErrors.concat(validate25.errors);
errors = vErrors.length;
}
var _valid0 = _errs2 === errors;
if(_valid0 && valid0){
valid0 = false;
passing0 = [passing0, 1];
}
else {
if(_valid0){
valid0 = true;
passing0 = 1;
if(props0 !== true){
props0 = true;
}
}
}
if(!valid0){
const err0 = {instancePath,schemaPath:"#/oneOf",keyword:"oneOf",params:{passingSchemas: passing0},message:"must match exactly one schema in oneOf"};
if(vErrors === null){
vErrors = [err0];
}
else {
vErrors.push(err0);
}
errors++;
validate22.errors = vErrors;
return false;
}
else {
errors = _errs0;
if(vErrors !== null){
if(_errs0){
vErrors.length = _errs0;
}
else {
vErrors = null;
}
}
}
validate22.errors = vErrors;
evaluated0.props = props0;
return errors === 0;
}
validate22.evaluated = {"dynamicProps":true,"dynamicItems":false};

const validateCategoricalRenderSpecRaw = validate27;
const schema42 = {"$id":"urn:patent-analysis:categorical-render-spec:1.0.0","title":"Categorical RenderSpec 1.0.0","type":"object","required":["render_spec_contract_version","renderer_kind","locale","timezone","width","height","font_family","animation","axis_label_max_graphemes","echarts_version","render_profile_id"],"additionalProperties":false,"properties":{"render_spec_contract_version":{"const":"1.0.0"},"renderer_kind":{"enum":["series.line.svg","series.stacked-bar.svg","composition.bar.svg","composition.pie.svg"]},"locale":{"const":"ja-JP"},"timezone":{"const":"UTC"},"width":{"const":1200},"height":{"const":675},"font_family":{"const":"Yu Gothic UI, Yu Gothic, Meiryo, sans-serif"},"animation":{"const":false},"axis_label_max_graphemes":{"const":28},"echarts_version":{"const":"6.1.0"},"render_profile_id":{"const":"categorical-svg-ja-jp-node22-echarts6.v1"}}};

function validate27(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
/*# sourceURL="urn:patent-analysis:categorical-render-spec:1.0.0" */;
let vErrors = null;
let errors = 0;
const evaluated0 = validate27.evaluated;
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
validate27.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!(func5.call(schema42.properties, key0))){
validate27.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.render_spec_contract_version !== undefined){
const _errs2 = errors;
if("1.0.0" !== data.render_spec_contract_version){
validate27.errors = [{instancePath:instancePath+"/render_spec_contract_version",schemaPath:"#/properties/render_spec_contract_version/const",keyword:"const",params:{allowedValue: "1.0.0"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.renderer_kind !== undefined){
let data1 = data.renderer_kind;
const _errs3 = errors;
if(!((((data1 === "series.line.svg") || (data1 === "series.stacked-bar.svg")) || (data1 === "composition.bar.svg")) || (data1 === "composition.pie.svg"))){
validate27.errors = [{instancePath:instancePath+"/renderer_kind",schemaPath:"#/properties/renderer_kind/enum",keyword:"enum",params:{allowedValues: schema42.properties.renderer_kind.enum},message:"must be equal to one of the allowed values"}];
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
validate27.errors = [{instancePath:instancePath+"/locale",schemaPath:"#/properties/locale/const",keyword:"const",params:{allowedValue: "ja-JP"},message:"must be equal to constant"}];
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
validate27.errors = [{instancePath:instancePath+"/timezone",schemaPath:"#/properties/timezone/const",keyword:"const",params:{allowedValue: "UTC"},message:"must be equal to constant"}];
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
validate27.errors = [{instancePath:instancePath+"/width",schemaPath:"#/properties/width/const",keyword:"const",params:{allowedValue: 1200},message:"must be equal to constant"}];
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
validate27.errors = [{instancePath:instancePath+"/height",schemaPath:"#/properties/height/const",keyword:"const",params:{allowedValue: 675},message:"must be equal to constant"}];
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
validate27.errors = [{instancePath:instancePath+"/font_family",schemaPath:"#/properties/font_family/const",keyword:"const",params:{allowedValue: "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif"},message:"must be equal to constant"}];
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
validate27.errors = [{instancePath:instancePath+"/animation",schemaPath:"#/properties/animation/const",keyword:"const",params:{allowedValue: false},message:"must be equal to constant"}];
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
validate27.errors = [{instancePath:instancePath+"/axis_label_max_graphemes",schemaPath:"#/properties/axis_label_max_graphemes/const",keyword:"const",params:{allowedValue: 28},message:"must be equal to constant"}];
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
validate27.errors = [{instancePath:instancePath+"/echarts_version",schemaPath:"#/properties/echarts_version/const",keyword:"const",params:{allowedValue: "6.1.0"},message:"must be equal to constant"}];
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
if("categorical-svg-ja-jp-node22-echarts6.v1" !== data.render_profile_id){
validate27.errors = [{instancePath:instancePath+"/render_profile_id",schemaPath:"#/properties/render_profile_id/const",keyword:"const",params:{allowedValue: "categorical-svg-ja-jp-node22-echarts6.v1"},message:"must be equal to constant"}];
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
validate27.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate27.errors = vErrors;
return errors === 0;
}
validate27.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const categoricalSegmenter = new Intl.Segmenter("ja-JP", { granularity: "grapheme" });

function graphemeCount(value) {
  let count = 0;
  for (const _segment of categoricalSegmenter.segment(value)) count += 1;
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
  if (!validateCategoricalChartModelRaw(value) || !safeText(value.title)) return false;
  let displayGraphemes = graphemeCount(value.title);
  if (value.chart_type === "series.line" || value.chart_type === "series.stacked-bar") {
    const expectedMark = value.chart_type === "series.line" ? "series-line-svg.v1" : "series-stacked-bar-svg.v1";
    if (value.mark !== expectedMark) return false;
    for (const label of value.x) {
      if (!safeText(label)) return false;
      displayGraphemes += graphemeCount(label);
    }
    const labels = new Set();
    for (const series of value.series) {
      if (!safeText(series.label) || labels.has(series.label)) return false;
      labels.add(series.label);
      displayGraphemes += graphemeCount(series.label);
      if (series.values.length !== value.x.length || series.row_counts.length !== value.x.length) return false;
      if (series.row_counts.some((count) => count > value.population.analyzed_rows)) return false;
    }
  } else {
    const expectedMark = value.chart_type === "composition.bar" ? "composition-bar-svg.v1" : "composition-pie-svg.v1";
    if (value.mark !== expectedMark) return false;
    const labels = new Set();
    for (const item of value.items) {
      if (!safeText(item.label) || labels.has(item.label) || item.row_count > value.population.analyzed_rows) return false;
      labels.add(item.label);
      displayGraphemes += graphemeCount(item.label);
    }
  }
  for (const warning of value.warnings) {
    if (!safeText(warning)) return false;
    displayGraphemes += graphemeCount(warning);
  }
  if (displayGraphemes > 20_000) return false;
  return value.population.input_rows === value.population.analyzed_rows + value.population.excluded_rows;
}

export function validateRenderSpec(value) {
  return validateCategoricalRenderSpecRaw(value);
}
