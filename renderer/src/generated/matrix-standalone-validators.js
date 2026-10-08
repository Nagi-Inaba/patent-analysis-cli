/* eslint-disable */
/* Generated validators enforce the closed neutral Matrix ChartModel contract. */
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
const schema32 = {"$id":"urn:patent-analysis:matrix-renderer-runtime:1.0.0","type":"object","additionalProperties":false,"required":["node_version","echarts_version","renderer_build_digest","render_profile_id"],"properties":{"node_version":{"const":"22.19.0"},"echarts_version":{"const":"6.1.0"},"renderer_build_digest":{"type":"string","pattern":"^[0-9a-f]{64}$"},"render_profile_id":{"const":"matrix-svg-ja-jp-node22-echarts6.v1"}}};

function validate21(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
/*# sourceURL="urn:patent-analysis:matrix-renderer-runtime:1.0.0" */;
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
if("matrix-svg-ja-jp-node22-echarts6.v1" !== data.render_profile_id){
validate21.errors = [{instancePath:instancePath+"/render_profile_id",schemaPath:"#/properties/render_profile_id/const",keyword:"const",params:{allowedValue: "matrix-svg-ja-jp-node22-echarts6.v1"},message:"must be equal to constant"}];
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

const validateMatrixChartModelRaw = validate22;
const schema33 = {"$defs":{"axis":{"additionalProperties":false,"properties":{"categories":{"items":{"$ref":"#/$defs/category"},"maxItems":101,"type":"array"},"role":{"maxLength":64,"minLength":1,"type":"string"}},"required":["role","categories"],"type":"object"},"category":{"additionalProperties":false,"properties":{"count":{"minimum":0,"type":"integer"},"id":{"pattern":"^[xy]:[0-9]+$","type":"string"},"index":{"maximum":100,"minimum":0,"type":"integer"},"is_other":{"type":"boolean"},"label":{"minLength":1,"type":"string"}},"required":["id","index","label","count","is_other"],"type":"object"},"cell":{"additionalProperties":false,"properties":{"row_count":{"minimum":1,"type":"integer"},"value":{"minimum":1,"type":"integer"},"x_index":{"maximum":100,"minimum":0,"type":"integer"},"x_label":{"minLength":1,"type":"string"},"y_index":{"maximum":100,"minimum":0,"type":"integer"},"y_label":{"minLength":1,"type":"string"}},"required":["x_index","y_index","x_label","y_label","value","row_count"],"type":"object"}},"$id":"urn:patent-analysis:matrix-chart-model:1.0.0","additionalProperties":false,"properties":{"analysis_result_sha256":{"pattern":"^[0-9a-f]{64}$","type":"string"},"cells":{"items":{"$ref":"#/$defs/cell"},"maxItems":400,"type":"array"},"chart_model_contract_version":{"const":"1.0.0"},"chart_type":{"enum":["matrix.bubble","matrix.heatmap"]},"mark":{"enum":["matrix-bubble-svg.v1","matrix-heatmap-svg.v1"]},"population":{"additionalProperties":false,"properties":{"analyzed_rows":{"minimum":0,"type":"integer"},"excluded_rows":{"minimum":0,"type":"integer"},"input_rows":{"minimum":0,"type":"integer"}},"required":["input_rows","analyzed_rows","excluded_rows"],"type":"object"},"title":{"maxLength":256,"minLength":1,"type":"string"},"warnings":{"items":{"type":"string"},"type":"array"},"x_axis":{"$ref":"#/$defs/axis"},"y_axis":{"$ref":"#/$defs/axis"}},"required":["chart_model_contract_version","chart_type","mark","analysis_result_sha256","title","x_axis","y_axis","cells","population","warnings"],"type":"object"};
const schema34 = {"additionalProperties":false,"properties":{"row_count":{"minimum":1,"type":"integer"},"value":{"minimum":1,"type":"integer"},"x_index":{"maximum":100,"minimum":0,"type":"integer"},"x_label":{"minLength":1,"type":"string"},"y_index":{"maximum":100,"minimum":0,"type":"integer"},"y_label":{"minLength":1,"type":"string"}},"required":["x_index","y_index","x_label","y_label","value","row_count"],"type":"object"};
const func5 = Object.prototype.hasOwnProperty;
const schema35 = {"additionalProperties":false,"properties":{"categories":{"items":{"$ref":"#/$defs/category"},"maxItems":101,"type":"array"},"role":{"maxLength":64,"minLength":1,"type":"string"}},"required":["role","categories"],"type":"object"};
const schema36 = {"additionalProperties":false,"properties":{"count":{"minimum":0,"type":"integer"},"id":{"pattern":"^[xy]:[0-9]+$","type":"string"},"index":{"maximum":100,"minimum":0,"type":"integer"},"is_other":{"type":"boolean"},"label":{"minLength":1,"type":"string"}},"required":["id","index","label","count","is_other"],"type":"object"};
const pattern10 = new RegExp("^[xy]:[0-9]+$", "u");

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
if(((data.role === undefined) && (missing0 = "role")) || ((data.categories === undefined) && (missing0 = "categories"))){
validate23.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!((key0 === "categories") || (key0 === "role"))){
validate23.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.categories !== undefined){
let data0 = data.categories;
const _errs2 = errors;
if(errors === _errs2){
if(Array.isArray(data0)){
if(data0.length > 101){
validate23.errors = [{instancePath:instancePath+"/categories",schemaPath:"#/properties/categories/maxItems",keyword:"maxItems",params:{limit: 101},message:"must NOT have more than 101 items"}];
return false;
}
else {
var valid1 = true;
const len0 = data0.length;
for(let i0=0; i0<len0; i0++){
let data1 = data0[i0];
const _errs4 = errors;
const _errs5 = errors;
if(errors === _errs5){
if(data1 && typeof data1 == "object" && !Array.isArray(data1)){
let missing1;
if((((((data1.id === undefined) && (missing1 = "id")) || ((data1.index === undefined) && (missing1 = "index"))) || ((data1.label === undefined) && (missing1 = "label"))) || ((data1.count === undefined) && (missing1 = "count"))) || ((data1.is_other === undefined) && (missing1 = "is_other"))){
validate23.errors = [{instancePath:instancePath+"/categories/" + i0,schemaPath:"#/$defs/category/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
const _errs7 = errors;
for(const key1 in data1){
if(!(((((key1 === "count") || (key1 === "id")) || (key1 === "index")) || (key1 === "is_other")) || (key1 === "label"))){
validate23.errors = [{instancePath:instancePath+"/categories/" + i0,schemaPath:"#/$defs/category/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs7 === errors){
if(data1.count !== undefined){
let data2 = data1.count;
const _errs8 = errors;
if(!(((typeof data2 == "number") && (!(data2 % 1) && !isNaN(data2))) && (isFinite(data2)))){
validate23.errors = [{instancePath:instancePath+"/categories/" + i0+"/count",schemaPath:"#/$defs/category/properties/count/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs8){
if((typeof data2 == "number") && (isFinite(data2))){
if(data2 < 0 || isNaN(data2)){
validate23.errors = [{instancePath:instancePath+"/categories/" + i0+"/count",schemaPath:"#/$defs/category/properties/count/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid3 = _errs8 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.id !== undefined){
let data3 = data1.id;
const _errs10 = errors;
if(errors === _errs10){
if(typeof data3 === "string"){
if(!pattern10.test(data3)){
validate23.errors = [{instancePath:instancePath+"/categories/" + i0+"/id",schemaPath:"#/$defs/category/properties/id/pattern",keyword:"pattern",params:{pattern: "^[xy]:[0-9]+$"},message:"must match pattern \""+"^[xy]:[0-9]+$"+"\""}];
return false;
}
}
else {
validate23.errors = [{instancePath:instancePath+"/categories/" + i0+"/id",schemaPath:"#/$defs/category/properties/id/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid3 = _errs10 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.index !== undefined){
let data4 = data1.index;
const _errs12 = errors;
if(!(((typeof data4 == "number") && (!(data4 % 1) && !isNaN(data4))) && (isFinite(data4)))){
validate23.errors = [{instancePath:instancePath+"/categories/" + i0+"/index",schemaPath:"#/$defs/category/properties/index/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs12){
if((typeof data4 == "number") && (isFinite(data4))){
if(data4 > 100 || isNaN(data4)){
validate23.errors = [{instancePath:instancePath+"/categories/" + i0+"/index",schemaPath:"#/$defs/category/properties/index/maximum",keyword:"maximum",params:{comparison: "<=", limit: 100},message:"must be <= 100"}];
return false;
}
else {
if(data4 < 0 || isNaN(data4)){
validate23.errors = [{instancePath:instancePath+"/categories/" + i0+"/index",schemaPath:"#/$defs/category/properties/index/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid3 = _errs12 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.is_other !== undefined){
const _errs14 = errors;
if(typeof data1.is_other !== "boolean"){
validate23.errors = [{instancePath:instancePath+"/categories/" + i0+"/is_other",schemaPath:"#/$defs/category/properties/is_other/type",keyword:"type",params:{type: "boolean"},message:"must be boolean"}];
return false;
}
var valid3 = _errs14 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data1.label !== undefined){
let data6 = data1.label;
const _errs16 = errors;
if(errors === _errs16){
if(typeof data6 === "string"){
if(func1(data6) < 1){
validate23.errors = [{instancePath:instancePath+"/categories/" + i0+"/label",schemaPath:"#/$defs/category/properties/label/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
else {
validate23.errors = [{instancePath:instancePath+"/categories/" + i0+"/label",schemaPath:"#/$defs/category/properties/label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid3 = _errs16 === errors;
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
else {
validate23.errors = [{instancePath:instancePath+"/categories/" + i0,schemaPath:"#/$defs/category/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid1 = _errs4 === errors;
if(!valid1){
break;
}
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/categories",schemaPath:"#/properties/categories/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.role !== undefined){
let data7 = data.role;
const _errs18 = errors;
if(errors === _errs18){
if(typeof data7 === "string"){
if(func1(data7) > 64){
validate23.errors = [{instancePath:instancePath+"/role",schemaPath:"#/properties/role/maxLength",keyword:"maxLength",params:{limit: 64},message:"must NOT have more than 64 characters"}];
return false;
}
else {
if(func1(data7) < 1){
validate23.errors = [{instancePath:instancePath+"/role",schemaPath:"#/properties/role/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate23.errors = [{instancePath:instancePath+"/role",schemaPath:"#/properties/role/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs18 === errors;
}
else {
var valid0 = true;
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


function validate22(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
/*# sourceURL="urn:patent-analysis:matrix-chart-model:1.0.0" */;
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
if(((((((((((data.chart_model_contract_version === undefined) && (missing0 = "chart_model_contract_version")) || ((data.chart_type === undefined) && (missing0 = "chart_type"))) || ((data.mark === undefined) && (missing0 = "mark"))) || ((data.analysis_result_sha256 === undefined) && (missing0 = "analysis_result_sha256"))) || ((data.title === undefined) && (missing0 = "title"))) || ((data.x_axis === undefined) && (missing0 = "x_axis"))) || ((data.y_axis === undefined) && (missing0 = "y_axis"))) || ((data.cells === undefined) && (missing0 = "cells"))) || ((data.population === undefined) && (missing0 = "population"))) || ((data.warnings === undefined) && (missing0 = "warnings"))){
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
if(data.analysis_result_sha256 !== undefined){
let data0 = data.analysis_result_sha256;
const _errs2 = errors;
if(errors === _errs2){
if(typeof data0 === "string"){
if(!pattern5.test(data0)){
validate22.errors = [{instancePath:instancePath+"/analysis_result_sha256",schemaPath:"#/properties/analysis_result_sha256/pattern",keyword:"pattern",params:{pattern: "^[0-9a-f]{64}$"},message:"must match pattern \""+"^[0-9a-f]{64}$"+"\""}];
return false;
}
}
else {
validate22.errors = [{instancePath:instancePath+"/analysis_result_sha256",schemaPath:"#/properties/analysis_result_sha256/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.cells !== undefined){
let data1 = data.cells;
const _errs4 = errors;
if(errors === _errs4){
if(Array.isArray(data1)){
if(data1.length > 400){
validate22.errors = [{instancePath:instancePath+"/cells",schemaPath:"#/properties/cells/maxItems",keyword:"maxItems",params:{limit: 400},message:"must NOT have more than 400 items"}];
return false;
}
else {
var valid1 = true;
const len0 = data1.length;
for(let i0=0; i0<len0; i0++){
let data2 = data1[i0];
const _errs6 = errors;
const _errs7 = errors;
if(errors === _errs7){
if(data2 && typeof data2 == "object" && !Array.isArray(data2)){
let missing1;
if(((((((data2.x_index === undefined) && (missing1 = "x_index")) || ((data2.y_index === undefined) && (missing1 = "y_index"))) || ((data2.x_label === undefined) && (missing1 = "x_label"))) || ((data2.y_label === undefined) && (missing1 = "y_label"))) || ((data2.value === undefined) && (missing1 = "value"))) || ((data2.row_count === undefined) && (missing1 = "row_count"))){
validate22.errors = [{instancePath:instancePath+"/cells/" + i0,schemaPath:"#/$defs/cell/required",keyword:"required",params:{missingProperty: missing1},message:"must have required property '"+missing1+"'"}];
return false;
}
else {
const _errs9 = errors;
for(const key1 in data2){
if(!((((((key1 === "row_count") || (key1 === "value")) || (key1 === "x_index")) || (key1 === "x_label")) || (key1 === "y_index")) || (key1 === "y_label"))){
validate22.errors = [{instancePath:instancePath+"/cells/" + i0,schemaPath:"#/$defs/cell/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key1},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs9 === errors){
if(data2.row_count !== undefined){
let data3 = data2.row_count;
const _errs10 = errors;
if(!(((typeof data3 == "number") && (!(data3 % 1) && !isNaN(data3))) && (isFinite(data3)))){
validate22.errors = [{instancePath:instancePath+"/cells/" + i0+"/row_count",schemaPath:"#/$defs/cell/properties/row_count/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs10){
if((typeof data3 == "number") && (isFinite(data3))){
if(data3 < 1 || isNaN(data3)){
validate22.errors = [{instancePath:instancePath+"/cells/" + i0+"/row_count",schemaPath:"#/$defs/cell/properties/row_count/minimum",keyword:"minimum",params:{comparison: ">=", limit: 1},message:"must be >= 1"}];
return false;
}
}
}
var valid3 = _errs10 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data2.value !== undefined){
let data4 = data2.value;
const _errs12 = errors;
if(!(((typeof data4 == "number") && (!(data4 % 1) && !isNaN(data4))) && (isFinite(data4)))){
validate22.errors = [{instancePath:instancePath+"/cells/" + i0+"/value",schemaPath:"#/$defs/cell/properties/value/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs12){
if((typeof data4 == "number") && (isFinite(data4))){
if(data4 < 1 || isNaN(data4)){
validate22.errors = [{instancePath:instancePath+"/cells/" + i0+"/value",schemaPath:"#/$defs/cell/properties/value/minimum",keyword:"minimum",params:{comparison: ">=", limit: 1},message:"must be >= 1"}];
return false;
}
}
}
var valid3 = _errs12 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data2.x_index !== undefined){
let data5 = data2.x_index;
const _errs14 = errors;
if(!(((typeof data5 == "number") && (!(data5 % 1) && !isNaN(data5))) && (isFinite(data5)))){
validate22.errors = [{instancePath:instancePath+"/cells/" + i0+"/x_index",schemaPath:"#/$defs/cell/properties/x_index/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs14){
if((typeof data5 == "number") && (isFinite(data5))){
if(data5 > 100 || isNaN(data5)){
validate22.errors = [{instancePath:instancePath+"/cells/" + i0+"/x_index",schemaPath:"#/$defs/cell/properties/x_index/maximum",keyword:"maximum",params:{comparison: "<=", limit: 100},message:"must be <= 100"}];
return false;
}
else {
if(data5 < 0 || isNaN(data5)){
validate22.errors = [{instancePath:instancePath+"/cells/" + i0+"/x_index",schemaPath:"#/$defs/cell/properties/x_index/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
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
if(data2.x_label !== undefined){
let data6 = data2.x_label;
const _errs16 = errors;
if(errors === _errs16){
if(typeof data6 === "string"){
if(func1(data6) < 1){
validate22.errors = [{instancePath:instancePath+"/cells/" + i0+"/x_label",schemaPath:"#/$defs/cell/properties/x_label/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
else {
validate22.errors = [{instancePath:instancePath+"/cells/" + i0+"/x_label",schemaPath:"#/$defs/cell/properties/x_label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid3 = _errs16 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data2.y_index !== undefined){
let data7 = data2.y_index;
const _errs18 = errors;
if(!(((typeof data7 == "number") && (!(data7 % 1) && !isNaN(data7))) && (isFinite(data7)))){
validate22.errors = [{instancePath:instancePath+"/cells/" + i0+"/y_index",schemaPath:"#/$defs/cell/properties/y_index/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs18){
if((typeof data7 == "number") && (isFinite(data7))){
if(data7 > 100 || isNaN(data7)){
validate22.errors = [{instancePath:instancePath+"/cells/" + i0+"/y_index",schemaPath:"#/$defs/cell/properties/y_index/maximum",keyword:"maximum",params:{comparison: "<=", limit: 100},message:"must be <= 100"}];
return false;
}
else {
if(data7 < 0 || isNaN(data7)){
validate22.errors = [{instancePath:instancePath+"/cells/" + i0+"/y_index",schemaPath:"#/$defs/cell/properties/y_index/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
}
var valid3 = _errs18 === errors;
}
else {
var valid3 = true;
}
if(valid3){
if(data2.y_label !== undefined){
let data8 = data2.y_label;
const _errs20 = errors;
if(errors === _errs20){
if(typeof data8 === "string"){
if(func1(data8) < 1){
validate22.errors = [{instancePath:instancePath+"/cells/" + i0+"/y_label",schemaPath:"#/$defs/cell/properties/y_label/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
else {
validate22.errors = [{instancePath:instancePath+"/cells/" + i0+"/y_label",schemaPath:"#/$defs/cell/properties/y_label/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid3 = _errs20 === errors;
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
validate22.errors = [{instancePath:instancePath+"/cells/" + i0,schemaPath:"#/$defs/cell/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
var valid1 = _errs6 === errors;
if(!valid1){
break;
}
}
}
}
else {
validate22.errors = [{instancePath:instancePath+"/cells",schemaPath:"#/properties/cells/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.chart_model_contract_version !== undefined){
const _errs22 = errors;
if("1.0.0" !== data.chart_model_contract_version){
validate22.errors = [{instancePath:instancePath+"/chart_model_contract_version",schemaPath:"#/properties/chart_model_contract_version/const",keyword:"const",params:{allowedValue: "1.0.0"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs22 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.chart_type !== undefined){
let data10 = data.chart_type;
const _errs23 = errors;
if(!((data10 === "matrix.bubble") || (data10 === "matrix.heatmap"))){
validate22.errors = [{instancePath:instancePath+"/chart_type",schemaPath:"#/properties/chart_type/enum",keyword:"enum",params:{allowedValues: schema33.properties.chart_type.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid0 = _errs23 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.mark !== undefined){
let data11 = data.mark;
const _errs24 = errors;
if(!((data11 === "matrix-bubble-svg.v1") || (data11 === "matrix-heatmap-svg.v1"))){
validate22.errors = [{instancePath:instancePath+"/mark",schemaPath:"#/properties/mark/enum",keyword:"enum",params:{allowedValues: schema33.properties.mark.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid0 = _errs24 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.population !== undefined){
let data12 = data.population;
const _errs25 = errors;
if(errors === _errs25){
if(data12 && typeof data12 == "object" && !Array.isArray(data12)){
let missing2;
if((((data12.input_rows === undefined) && (missing2 = "input_rows")) || ((data12.analyzed_rows === undefined) && (missing2 = "analyzed_rows"))) || ((data12.excluded_rows === undefined) && (missing2 = "excluded_rows"))){
validate22.errors = [{instancePath:instancePath+"/population",schemaPath:"#/properties/population/required",keyword:"required",params:{missingProperty: missing2},message:"must have required property '"+missing2+"'"}];
return false;
}
else {
const _errs27 = errors;
for(const key2 in data12){
if(!(((key2 === "analyzed_rows") || (key2 === "excluded_rows")) || (key2 === "input_rows"))){
validate22.errors = [{instancePath:instancePath+"/population",schemaPath:"#/properties/population/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key2},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs27 === errors){
if(data12.analyzed_rows !== undefined){
let data13 = data12.analyzed_rows;
const _errs28 = errors;
if(!(((typeof data13 == "number") && (!(data13 % 1) && !isNaN(data13))) && (isFinite(data13)))){
validate22.errors = [{instancePath:instancePath+"/population/analyzed_rows",schemaPath:"#/properties/population/properties/analyzed_rows/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs28){
if((typeof data13 == "number") && (isFinite(data13))){
if(data13 < 0 || isNaN(data13)){
validate22.errors = [{instancePath:instancePath+"/population/analyzed_rows",schemaPath:"#/properties/population/properties/analyzed_rows/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid4 = _errs28 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data12.excluded_rows !== undefined){
let data14 = data12.excluded_rows;
const _errs30 = errors;
if(!(((typeof data14 == "number") && (!(data14 % 1) && !isNaN(data14))) && (isFinite(data14)))){
validate22.errors = [{instancePath:instancePath+"/population/excluded_rows",schemaPath:"#/properties/population/properties/excluded_rows/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs30){
if((typeof data14 == "number") && (isFinite(data14))){
if(data14 < 0 || isNaN(data14)){
validate22.errors = [{instancePath:instancePath+"/population/excluded_rows",schemaPath:"#/properties/population/properties/excluded_rows/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid4 = _errs30 === errors;
}
else {
var valid4 = true;
}
if(valid4){
if(data12.input_rows !== undefined){
let data15 = data12.input_rows;
const _errs32 = errors;
if(!(((typeof data15 == "number") && (!(data15 % 1) && !isNaN(data15))) && (isFinite(data15)))){
validate22.errors = [{instancePath:instancePath+"/population/input_rows",schemaPath:"#/properties/population/properties/input_rows/type",keyword:"type",params:{type: "integer"},message:"must be integer"}];
return false;
}
if(errors === _errs32){
if((typeof data15 == "number") && (isFinite(data15))){
if(data15 < 0 || isNaN(data15)){
validate22.errors = [{instancePath:instancePath+"/population/input_rows",schemaPath:"#/properties/population/properties/input_rows/minimum",keyword:"minimum",params:{comparison: ">=", limit: 0},message:"must be >= 0"}];
return false;
}
}
}
var valid4 = _errs32 === errors;
}
else {
var valid4 = true;
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
var valid0 = _errs25 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.title !== undefined){
let data16 = data.title;
const _errs34 = errors;
if(errors === _errs34){
if(typeof data16 === "string"){
if(func1(data16) > 256){
validate22.errors = [{instancePath:instancePath+"/title",schemaPath:"#/properties/title/maxLength",keyword:"maxLength",params:{limit: 256},message:"must NOT have more than 256 characters"}];
return false;
}
else {
if(func1(data16) < 1){
validate22.errors = [{instancePath:instancePath+"/title",schemaPath:"#/properties/title/minLength",keyword:"minLength",params:{limit: 1},message:"must NOT have fewer than 1 characters"}];
return false;
}
}
}
else {
validate22.errors = [{instancePath:instancePath+"/title",schemaPath:"#/properties/title/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
}
var valid0 = _errs34 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.warnings !== undefined){
let data17 = data.warnings;
const _errs36 = errors;
if(errors === _errs36){
if(Array.isArray(data17)){
var valid5 = true;
const len1 = data17.length;
for(let i1=0; i1<len1; i1++){
const _errs38 = errors;
if(typeof data17[i1] !== "string"){
validate22.errors = [{instancePath:instancePath+"/warnings/" + i1,schemaPath:"#/properties/warnings/items/type",keyword:"type",params:{type: "string"},message:"must be string"}];
return false;
}
var valid5 = _errs38 === errors;
if(!valid5){
break;
}
}
}
else {
validate22.errors = [{instancePath:instancePath+"/warnings",schemaPath:"#/properties/warnings/type",keyword:"type",params:{type: "array"},message:"must be array"}];
return false;
}
}
var valid0 = _errs36 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.x_axis !== undefined){
const _errs40 = errors;
if(!(validate23(data.x_axis, {instancePath:instancePath+"/x_axis",parentData:data,parentDataProperty:"x_axis",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate23.errors : vErrors.concat(validate23.errors);
errors = vErrors.length;
}
var valid0 = _errs40 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.y_axis !== undefined){
const _errs41 = errors;
if(!(validate23(data.y_axis, {instancePath:instancePath+"/y_axis",parentData:data,parentDataProperty:"y_axis",rootData,dynamicAnchors}))){
vErrors = vErrors === null ? validate23.errors : vErrors.concat(validate23.errors);
errors = vErrors.length;
}
var valid0 = _errs41 === errors;
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

const validateMatrixRenderSpecRaw = validate26;
const schema37 = {"$id":"urn:patent-analysis:matrix-render-spec:1.0.0","additionalProperties":false,"properties":{"animation":{"const":false},"axis_label_max_graphemes":{"const":28},"echarts_version":{"const":"6.1.0"},"font_family":{"const":"Yu Gothic UI, Yu Gothic, Meiryo, sans-serif"},"height":{"const":675},"locale":{"const":"ja-JP"},"render_profile_id":{"const":"matrix-svg-ja-jp-node22-echarts6.v1"},"render_spec_contract_version":{"const":"1.0.0"},"renderer_kind":{"enum":["matrix.bubble.svg","matrix.heatmap.svg"]},"timezone":{"const":"UTC"},"width":{"const":1200}},"required":["render_spec_contract_version","renderer_kind","locale","timezone","width","height","font_family","animation","axis_label_max_graphemes","echarts_version","render_profile_id"],"type":"object"};

function validate26(data, {instancePath="", parentData, parentDataProperty, rootData=data, dynamicAnchors={}}={}){
/*# sourceURL="urn:patent-analysis:matrix-render-spec:1.0.0" */;
let vErrors = null;
let errors = 0;
const evaluated0 = validate26.evaluated;
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
validate26.errors = [{instancePath,schemaPath:"#/required",keyword:"required",params:{missingProperty: missing0},message:"must have required property '"+missing0+"'"}];
return false;
}
else {
const _errs1 = errors;
for(const key0 in data){
if(!(func5.call(schema37.properties, key0))){
validate26.errors = [{instancePath,schemaPath:"#/additionalProperties",keyword:"additionalProperties",params:{additionalProperty: key0},message:"must NOT have additional properties"}];
return false;
break;
}
}
if(_errs1 === errors){
if(data.animation !== undefined){
const _errs2 = errors;
if(false !== data.animation){
validate26.errors = [{instancePath:instancePath+"/animation",schemaPath:"#/properties/animation/const",keyword:"const",params:{allowedValue: false},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs2 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.axis_label_max_graphemes !== undefined){
const _errs3 = errors;
if(28 !== data.axis_label_max_graphemes){
validate26.errors = [{instancePath:instancePath+"/axis_label_max_graphemes",schemaPath:"#/properties/axis_label_max_graphemes/const",keyword:"const",params:{allowedValue: 28},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs3 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.echarts_version !== undefined){
const _errs4 = errors;
if("6.1.0" !== data.echarts_version){
validate26.errors = [{instancePath:instancePath+"/echarts_version",schemaPath:"#/properties/echarts_version/const",keyword:"const",params:{allowedValue: "6.1.0"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs4 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.font_family !== undefined){
const _errs5 = errors;
if("Yu Gothic UI, Yu Gothic, Meiryo, sans-serif" !== data.font_family){
validate26.errors = [{instancePath:instancePath+"/font_family",schemaPath:"#/properties/font_family/const",keyword:"const",params:{allowedValue: "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs5 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.height !== undefined){
const _errs6 = errors;
if(675 !== data.height){
validate26.errors = [{instancePath:instancePath+"/height",schemaPath:"#/properties/height/const",keyword:"const",params:{allowedValue: 675},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs6 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.locale !== undefined){
const _errs7 = errors;
if("ja-JP" !== data.locale){
validate26.errors = [{instancePath:instancePath+"/locale",schemaPath:"#/properties/locale/const",keyword:"const",params:{allowedValue: "ja-JP"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs7 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.render_profile_id !== undefined){
const _errs8 = errors;
if("matrix-svg-ja-jp-node22-echarts6.v1" !== data.render_profile_id){
validate26.errors = [{instancePath:instancePath+"/render_profile_id",schemaPath:"#/properties/render_profile_id/const",keyword:"const",params:{allowedValue: "matrix-svg-ja-jp-node22-echarts6.v1"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs8 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.render_spec_contract_version !== undefined){
const _errs9 = errors;
if("1.0.0" !== data.render_spec_contract_version){
validate26.errors = [{instancePath:instancePath+"/render_spec_contract_version",schemaPath:"#/properties/render_spec_contract_version/const",keyword:"const",params:{allowedValue: "1.0.0"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs9 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.renderer_kind !== undefined){
let data8 = data.renderer_kind;
const _errs10 = errors;
if(!((data8 === "matrix.bubble.svg") || (data8 === "matrix.heatmap.svg"))){
validate26.errors = [{instancePath:instancePath+"/renderer_kind",schemaPath:"#/properties/renderer_kind/enum",keyword:"enum",params:{allowedValues: schema37.properties.renderer_kind.enum},message:"must be equal to one of the allowed values"}];
return false;
}
var valid0 = _errs10 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.timezone !== undefined){
const _errs11 = errors;
if("UTC" !== data.timezone){
validate26.errors = [{instancePath:instancePath+"/timezone",schemaPath:"#/properties/timezone/const",keyword:"const",params:{allowedValue: "UTC"},message:"must be equal to constant"}];
return false;
}
var valid0 = _errs11 === errors;
}
else {
var valid0 = true;
}
if(valid0){
if(data.width !== undefined){
const _errs12 = errors;
if(1200 !== data.width){
validate26.errors = [{instancePath:instancePath+"/width",schemaPath:"#/properties/width/const",keyword:"const",params:{allowedValue: 1200},message:"must be equal to constant"}];
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
validate26.errors = [{instancePath,schemaPath:"#/type",keyword:"type",params:{type: "object"},message:"must be object"}];
return false;
}
}
validate26.errors = vErrors;
return errors === 0;
}
validate26.evaluated = {"props":true,"dynamicProps":false,"dynamicItems":false};

const matrixSegmenter = new Intl.Segmenter("ja-JP", { granularity: "grapheme" });

function matrixGraphemeCount(value) {
  let count = 0;
  for (const _segment of matrixSegmenter.segment(value)) count += 1;
  return count;
}

function matrixSafeText(value) {
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
  if (!validateMatrixChartModelRaw(value)) return false;
  if (!matrixSafeText(value.title)) return false;
  let displayGraphemes = matrixGraphemeCount(value.title);
  const xIds = new Set();
  const yIds = new Set();
  for (let index = 0; index < value.x_axis.categories.length; index += 1) {
    const category = value.x_axis.categories[index];
    if (
      category.index !== index ||
      category.id !== "x:" + index ||
      xIds.has(category.id) ||
      !matrixSafeText(category.label)
    ) return false;
    xIds.add(category.id);
    displayGraphemes += matrixGraphemeCount(category.label);
  }
  for (let index = 0; index < value.y_axis.categories.length; index += 1) {
    const category = value.y_axis.categories[index];
    if (
      category.index !== index ||
      category.id !== "y:" + index ||
      yIds.has(category.id) ||
      !matrixSafeText(category.label)
    ) return false;
    yIds.add(category.id);
    displayGraphemes += matrixGraphemeCount(category.label);
  }
  const pairs = new Set();
  for (const cell of value.cells) {
    if (
      cell.x_index >= value.x_axis.categories.length ||
      cell.y_index >= value.y_axis.categories.length ||
      cell.x_label !== value.x_axis.categories[cell.x_index].label ||
      cell.y_label !== value.y_axis.categories[cell.y_index].label ||
      cell.value !== cell.row_count ||
      cell.row_count > value.population.analyzed_rows
    ) return false;
    const pair = String(cell.y_index) + "\u0000" + String(cell.x_index);
    if (pairs.has(pair)) return false;
    pairs.add(pair);
  }
  for (const warning of value.warnings) {
    if (!matrixSafeText(warning)) return false;
    displayGraphemes += matrixGraphemeCount(warning);
  }
  if (displayGraphemes > 20_000) return false;
  const population = value.population;
  return population.input_rows === population.analyzed_rows + population.excluded_rows;
}

export function validateRenderSpec(value) {
  return validateMatrixRenderSpecRaw(value);
}
