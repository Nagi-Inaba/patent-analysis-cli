import { DOMParser } from "@xmldom/xmldom";
import type { Document, Element, Node } from "@xmldom/xmldom";

const SVG_NAMESPACE = "http://www.w3.org/2000/svg";
const XMLNS_NAMESPACE = "http://www.w3.org/2000/xmlns/";
const XLINK_NAMESPACE = "http://www.w3.org/1999/xlink";
const XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace";

const ALLOWED_ATTRIBUTES = Object.freeze<Record<string, ReadonlySet<string>>>({
  svg: new Set(["height", "viewBox", "width", "xmlns"]),
  g: new Set(["clip-path", "fill", "id", "opacity", "stroke", "stroke-dasharray", "stroke-linecap", "stroke-linejoin", "stroke-width", "transform"]),
  defs: new Set(),
  clipPath: new Set(["id", "transform"]),
  rect: new Set(["clip-path", "fill", "height", "id", "opacity", "rx", "ry", "stroke", "stroke-dasharray", "stroke-linecap", "stroke-linejoin", "stroke-width", "transform", "width", "x", "y"]),
  path: new Set(["clip-path", "d", "fill", "id", "opacity", "stroke", "stroke-dasharray", "stroke-linecap", "stroke-linejoin", "stroke-miterlimit", "stroke-width", "transform"]),
  line: new Set(["clip-path", "id", "opacity", "stroke", "stroke-dasharray", "stroke-linecap", "stroke-width", "transform", "x1", "x2", "y1", "y2"]),
  polyline: new Set(["clip-path", "fill", "id", "opacity", "points", "stroke", "stroke-dasharray", "stroke-linecap", "stroke-linejoin", "stroke-width", "transform"]),
  polygon: new Set(["clip-path", "fill", "id", "opacity", "points", "stroke", "stroke-dasharray", "stroke-linecap", "stroke-linejoin", "stroke-width", "transform"]),
  circle: new Set(["clip-path", "cx", "cy", "fill", "id", "opacity", "r", "stroke", "stroke-dasharray", "stroke-width", "transform"]),
  ellipse: new Set(["clip-path", "cx", "cy", "fill", "id", "opacity", "rx", "ry", "stroke", "stroke-dasharray", "stroke-width", "transform"]),
  text: new Set(["xml:space", "clip-path", "dominant-baseline", "dx", "dy", "fill", "font-family", "font-size", "font-weight", "id", "opacity", "text-anchor", "transform", "x", "y"]),
  tspan: new Set(["xml:space", "dominant-baseline", "dx", "dy", "fill", "font-family", "font-size", "font-weight", "opacity", "text-anchor", "x", "y"])
});

const TRANSIENT_ATTRIBUTES = new Set([
  "class",
  "style",
  "pointer-events",
  "ecmeta_series_index",
  "ecmeta_data_index",
  "ecmeta_ssr_type",
  "ecmeta_silent",
  "fill-opacity",
  "stroke-opacity"
]);
const CONTAINER_ELEMENTS = new Set(["svg", "g", "defs", "clipPath"]);
const TEXT_ELEMENTS = new Set(["text", "tspan"]);
const CLASS_NAME = /^zr[0-9]+-cls-[0-9]+$/u;
const ID_NAME = /^[A-Za-z][A-Za-z0-9_-]{0,127}$/u;
const NUMBER = /^-?(?:0|[1-9][0-9]*)(?:\.[0-9]{1,12})?$/u;
const NEGATIVE_ZERO = /^-0(?:\.0+)?$/u;
const NUMERIC_ATTRIBUTES = new Set([
  "x", "y", "x1", "x2", "y1", "y2", "cx", "cy", "dx", "dy"
]);
const NONNEGATIVE_ATTRIBUTES = new Set(["width", "height", "r", "rx", "ry"]);
const PAINT = /^(?:none|transparent|#[0-9A-Fa-f]{3}|#[0-9A-Fa-f]{6}|rgb\((?:0|[1-9][0-9]?|1[0-9]{2}|2[0-4][0-9]|25[0-5]),(?:0|[1-9][0-9]?|1[0-9]{2}|2[0-4][0-9]|25[0-5]),(?:0|[1-9][0-9]?|1[0-9]{2}|2[0-4][0-9]|25[0-5])\)|rgba\((?:0|[1-9][0-9]?|1[0-9]{2}|2[0-4][0-9]|25[0-5]),(?:0|[1-9][0-9]?|1[0-9]{2}|2[0-4][0-9]|25[0-5]),(?:0|[1-9][0-9]?|1[0-9]{2}|2[0-4][0-9]|25[0-5]),(?:0|1|0\.[0-9]{1,6})\))$/u;
const PATH_ARITY: Readonly<Record<string, number>> = Object.freeze({
  M: 2, m: 2, L: 2, l: 2, H: 1, h: 1, V: 1, v: 1,
  C: 6, c: 6, S: 4, s: 4, Q: 4, q: 4, T: 2, t: 2,
  A: 7, a: 7, Z: 0, z: 0
});
const MAX_SVG_UTF8_BYTES = 8 * 1024 * 1024;
const MAX_SVG_NODES = 50_000;
const MAX_SVG_ATTRIBUTES = 250_000;
const MAX_SVG_DEPTH = 64;
const MAX_TEXT_NODE_CODE_POINTS = 4096;
const MAX_TOTAL_TEXT_CODE_POINTS = 20_000;
const MAX_PATH_BYTES = 1024 * 1024;
const MAX_TOTAL_PATH_BYTES = 4 * 1024 * 1024;

function reject(message: string): never {
  throw new Error(`SVG normalization rejected: ${message}`);
}

function isPolicyNumber(value: string): boolean {
  return NUMBER.test(value) && !NEGATIVE_ZERO.test(value);
}

function utf8ByteLength(value: string): number {
  let bytes = 0;
  for (const character of value) {
    const codePoint = character.codePointAt(0)!;
    if (codePoint >= 0xD800 && codePoint <= 0xDFFF) reject("invalid UTF-8 text");
    bytes += codePoint <= 0x7F ? 1 : codePoint <= 0x7FF ? 2 : codePoint <= 0xFFFF ? 3 : 4;
  }
  return bytes;
}

function codePointCount(value: string): number {
  let count = 0;
  for (const character of value) count += character.length > 0 ? 1 : 0;
  return count;
}

function elementsInDocumentOrder(document: Document): Element[] {
  return Array.from(document.getElementsByTagName("*"));
}

function parseXml(rawSvg: string): Document {
  if (typeof rawSvg !== "string" || rawSvg.length === 0) {
    reject("invalid input size");
  }
  if (rawSvg.charCodeAt(0) === 0xFEFF) reject("UTF-8 BOM is forbidden");
  if (utf8ByteLength(rawSvg) > MAX_SVG_UTF8_BYTES) reject("UTF-8 byte budget exceeded");
  const upper = rawSvg.toUpperCase();
  for (const token of ["<!DOCTYPE", "<!ENTITY", "<?XML-STYLESHEET", "<![CDATA["]) {
    if (upper.includes(token)) reject("forbidden XML construct");
  }
  return new DOMParser({
    locator: false,
    onError: () => reject("malformed XML")
  }).parseFromString(rawSvg, "image/svg+xml");
}

function enforceDocumentBudgets(document: Document): void {
  const root = document.documentElement;
  if (root === null) reject("missing SVG root");
  let nodeCount = 0;
  let attributeCount = 0;
  let totalTextCodePoints = 0;
  let totalPathBytes = 0;
  const stack: Array<{ node: Node; depth: number }> = [{ node: root, depth: 1 }];
  while (stack.length > 0) {
    const current = stack.pop()!;
    nodeCount += 1;
    if (nodeCount > MAX_SVG_NODES) reject("node budget exceeded");
    if (current.depth > MAX_SVG_DEPTH) reject("depth budget exceeded");
    if (current.node.nodeType === 1) {
      const element = current.node as Element;
      attributeCount += element.attributes.length;
      if (attributeCount > MAX_SVG_ATTRIBUTES) reject("attribute budget exceeded");
      if (element.hasAttribute("d")) {
        const pathBytes = utf8ByteLength(element.getAttribute("d") ?? "");
        if (pathBytes > MAX_PATH_BYTES) reject("path byte budget exceeded");
        totalPathBytes += pathBytes;
        if (totalPathBytes > MAX_TOTAL_PATH_BYTES) reject("aggregate path budget exceeded");
      }
    } else if (current.node.nodeType === 3 || current.node.nodeType === 4) {
      const textCodePoints = codePointCount(current.node.nodeValue ?? "");
      if (textCodePoints > MAX_TEXT_NODE_CODE_POINTS) reject("text node budget exceeded");
      totalTextCodePoints += textCodePoints;
      if (totalTextCodePoints > MAX_TOTAL_TEXT_CODE_POINTS) reject("total text budget exceeded");
    }
    for (let index = current.node.childNodes.length - 1; index >= 0; index -= 1) {
      const child = current.node.childNodes.item(index);
      if (child !== null) stack.push({ node: child, depth: current.depth + 1 });
    }
  }
}

function parseDeclarations(source: string): Map<string, string> {
  if (source.includes("!important") || source.includes("/*") || source.includes("*/")) {
    reject("unsupported CSS priority or comment");
  }
  const declarations = new Map<string, string>();
  for (const piece of source.split(";")) {
    const declaration = piece.trim();
    if (declaration === "") continue;
    const separator = declaration.indexOf(":");
    if (separator <= 0 || declaration.indexOf(":", separator + 1) !== -1) {
      reject("malformed CSS declaration");
    }
    const property = declaration.slice(0, separator).trim();
    const value = declaration.slice(separator + 1).trim();
    if (value === "" || declarations.has(property)) reject("ambiguous CSS declaration");
    declarations.set(property, value);
  }
  return declarations;
}

function validateHoverDeclaration(property: string, value: string): void {
  if (property === "pointer-events" && value === "none") return;
  if (property === "cursor" && value === "pointer") return;
  if (
    property === "fill" &&
    /^rgba\((?:0|[1-9][0-9]?|1[0-9]{2}|2[0-4][0-9]|25[0-5]),(?:0|[1-9][0-9]?|1[0-9]{2}|2[0-4][0-9]|25[0-5]),(?:0|[1-9][0-9]?|1[0-9]{2}|2[0-4][0-9]|25[0-5]),1\)$/u.test(value)
  ) return;
  reject("unsupported hover declaration");
}

function validateStyleSheet(styleElement: Element): void {
  if (
    styleElement.namespaceURI !== SVG_NAMESPACE ||
    styleElement.prefix !== null ||
    styleElement.attributes.length !== 0
  ) reject("unknown style element metadata");
  const source = styleElement.textContent ?? "";
  let cursor = 0;
  while (cursor < source.length) {
    while (cursor < source.length && /\s/u.test(source[cursor]!)) cursor += 1;
    if (cursor === source.length) break;
    const open = source.indexOf("{", cursor);
    const close = source.indexOf("}", open + 1);
    if (open < 0 || close < 0 || source.indexOf("{", open + 1) !== -1 && source.indexOf("{", open + 1) < close) {
      reject("malformed CSS rule");
    }
    const selector = source.slice(cursor, open).trim();
    const selectorMatch = /^\.([A-Za-z0-9_-]+):hover$/u.exec(selector);
    if (selectorMatch === null || !CLASS_NAME.test(selectorMatch[1]!)) reject("unsupported CSS selector");
    const declarations = parseDeclarations(source.slice(open + 1, close));
    if (declarations.size === 0) reject("empty CSS rule");
    for (const [property, value] of declarations) validateHoverDeclaration(property, value);
    cursor = close + 1;
  }
}

function setEquivalentAttribute(element: Element, name: string, value: string): void {
  if (element.hasAttribute(name) && element.getAttribute(name) !== value) {
    reject("non-lossless presentation cascade");
  }
  element.setAttribute(name, value);
}

function materializeInlineStyle(element: Element): void {
  if (!element.hasAttribute("style")) return;
  const declarations = parseDeclarations(element.getAttribute("style") ?? "");
  for (const [property, value] of declarations) {
    if (property === "font-family" && value === "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif") {
      setEquivalentAttribute(element, "font-family", value);
      continue;
    }
    if (property === "font-size" && /^[0-9]+(?:\.[0-9]{1,12})?px$/u.test(value)) {
      const number = value.slice(0, -2);
      const numeric = Number(number);
      if (numeric >= 8 && numeric <= 96) {
        setEquivalentAttribute(element, "font-size", number);
        continue;
      }
    }
    if (property === "font-weight" && ["normal", "bold", "400", "500", "600", "700"].includes(value)) {
      setEquivalentAttribute(element, "font-weight", value);
      continue;
    }
    reject("unsupported inline presentation");
  }
  element.removeAttribute("style");
}

function normalizeTransform(value: string): string {
  let cursor = 0;
  const functions: string[] = [];
  while (cursor < value.length) {
    while (cursor < value.length && value[cursor] === " ") cursor += 1;
    const match = /^(matrix|translate|scale|rotate)\(/u.exec(value.slice(cursor));
    if (match === null) reject("unsupported transform");
    const name = match[1]!;
    const start = cursor + match[0].length;
    const end = value.indexOf(")", start);
    if (end < 0) reject("unterminated transform");
    const rawArguments = value.slice(start, end).trim();
    const argumentsList = rawArguments.split(/[ ,]+/u);
    const allowedArities: Record<string, number[]> = {
      matrix: [6], translate: [1, 2], scale: [1, 2], rotate: [1, 3]
    };
    if (
      !allowedArities[name]!.includes(argumentsList.length) ||
      argumentsList.some((item) => !isPolicyNumber(item) || Math.abs(Number(item)) > 1_000_000)
    ) {
      reject("invalid transform arguments");
    }
    functions.push(`${name}(${argumentsList.join(",")})`);
    if (functions.length > 16) reject("transform function budget exceeded");
    cursor = end + 1;
  }
  return functions.join(" ");
}

function normalizeDashArray(value: string): string {
  const values = value.split(/[ ,]+/u);
  if (
    values.length < 1 ||
    values.length > 16 ||
    values.some((item) => !isPolicyNumber(item) || Number(item) < 0 || Number(item) > 1_000_000)
  ) {
    reject("invalid dash array");
  }
  return values.join(" ");
}

function reduceOpacity(element: Element, attributeName: "fill-opacity" | "stroke-opacity"): void {
  if (!element.hasAttribute(attributeName)) return;
  const value = element.getAttribute(attributeName) ?? "";
  if (!isPolicyNumber(value) || Number(value) < 0 || Number(value) > 1) reject("invalid component opacity");
  if (value === "1") {
    element.removeAttribute(attributeName);
    return;
  }
  const otherPaintInvisible = attributeName === "fill-opacity"
    ? element.getAttribute("stroke") === "none" || element.getAttribute("stroke-width") === "0" || !element.hasAttribute("stroke")
    : element.getAttribute("fill") === "none";
  if (!otherPaintInvisible || element.hasAttribute("opacity")) reject("non-lossless component opacity");
  element.setAttribute("opacity", value);
  element.removeAttribute(attributeName);
}

function validatePath(value: string): void {
  if (value.length === 0 || value.length > 1_048_576) reject("invalid path size");
  const tokens: Array<{ kind: "command" | "number"; value: string }> = [];
  let cursor = 0;
  let previousWasNumber = false;
  while (cursor < value.length) {
    let separated = false;
    while (cursor < value.length && /[ \t\r\n,]/u.test(value[cursor]!)) {
      separated = true;
      cursor += 1;
    }
    if (cursor === value.length) break;
    const character = value[cursor]!;
    if (character in PATH_ARITY) {
      tokens.push({ kind: "command", value: character });
      cursor += 1;
      previousWasNumber = false;
      continue;
    }
    const numberMatch = /^-?(?:0|[1-9][0-9]*)(?:\.[0-9]{1,12})?/u.exec(value.slice(cursor));
    if (numberMatch === null || previousWasNumber && !separated) reject("invalid path token");
    const number = numberMatch[0];
    if (!isPolicyNumber(number) || Math.abs(Number(number)) > 1_000_000) reject("path coordinate out of range");
    tokens.push({ kind: "number", value: number });
    cursor += number.length;
    previousWasNumber = true;
  }
  if (tokens.length === 0 || tokens[0]!.kind !== "command" || !["M", "m"].includes(tokens[0]!.value)) {
    reject("path must begin with moveto");
  }
  let command: string | null = null;
  let argumentsList: string[] = [];
  let requiresArguments = false;
  let commandCount = 0;
  let argumentCount = 0;
  for (const token of tokens) {
    if (token.kind === "command") {
      if (argumentsList.length !== 0 || requiresArguments) reject("incomplete path command");
      command = token.value;
      if (PATH_ARITY[command] === 0) {
        commandCount += 1;
        command = null;
      } else {
        requiresArguments = true;
      }
      continue;
    }
    if (command === null) reject("path number without command");
    argumentsList.push(token.value);
    argumentCount += 1;
    const arity = PATH_ARITY[command]!;
    if (argumentsList.length === arity) {
      if (["A", "a"].includes(command)) {
        if (Number(argumentsList[0]) < 0 || Number(argumentsList[1]) < 0) reject("negative arc radius");
        if (!["0", "1"].includes(argumentsList[3]!) || !["0", "1"].includes(argumentsList[4]!)) {
          reject("invalid arc flag");
        }
      }
      commandCount += 1;
      requiresArguments = false;
      if (command === "M") command = "L";
      else if (command === "m") command = "l";
      argumentsList = [];
    }
    if (commandCount > 50_000 || argumentCount > 350_000) reject("path budget exceeded");
  }
  if (argumentsList.length !== 0 || requiresArguments) reject("incomplete path command");
}

function normalizePoints(value: string): string {
  let coordinates: string[] = [];
  if (value.length === 0 || value.startsWith(" ") || value.endsWith(" ")) {
    reject("invalid point list");
  }
  if (value.includes(",")) {
    const points = value.split(" ");
    if (points.length < 2 || points.length > 50_000 || points.some((point) => point.length === 0)) {
      reject("invalid point count");
    }
    for (const point of points) {
      const pair = point.split(",");
      if (pair.length !== 2) reject("invalid point list");
      coordinates.push(pair[0]!, pair[1]!);
    }
  } else {
    coordinates = value.split(" ");
    if (
      coordinates.length < 4 ||
      coordinates.length % 2 !== 0 ||
      coordinates.length > 100_000 ||
      coordinates.some((coordinate) => coordinate.length === 0)
    ) {
      reject("invalid point count");
    }
  }
  if (
    coordinates.some(
      (coordinate) =>
        !isPolicyNumber(coordinate) || Math.abs(Number(coordinate)) > 1_000_000
    )
  ) {
    reject("invalid point list");
  }
  const points: string[] = [];
  for (let index = 0; index < coordinates.length; index += 2) {
    points.push(`${coordinates[index]!},${coordinates[index + 1]!}`);
  }
  return points.join(" ");
}

function validateFinalAttribute(name: string, value: string): void {
  if (name === "xml:space") {
    if (value !== "preserve") reject("invalid whitespace preservation");
    return;
  }
  if (NUMERIC_ATTRIBUTES.has(name)) {
    if (!isPolicyNumber(value) || Math.abs(Number(value)) > 1_000_000) reject("invalid numeric attribute");
    return;
  }
  if (NONNEGATIVE_ATTRIBUTES.has(name)) {
    if (!isPolicyNumber(value) || Number(value) < 0 || Number(value) > 1_000_000) reject("invalid size attribute");
    return;
  }
  if (name === "viewBox") {
    const values = value.split(" ");
    if (
      values.length !== 4 ||
      values.some((item) => !isPolicyNumber(item) || Math.abs(Number(item)) > 1_000_000) ||
      Number(values[2]) <= 0 || Number(values[3]) <= 0
    ) reject("invalid viewBox");
    return;
  }
  if (name === "fill" || name === "stroke") {
    if (!PAINT.test(value)) reject("invalid paint");
    return;
  }
  if (name === "opacity") {
    if (!isPolicyNumber(value) || Number(value) < 0 || Number(value) > 1) reject("invalid opacity");
    return;
  }
  if (name === "stroke-width") {
    if (!isPolicyNumber(value) || Number(value) < 0 || Number(value) > 1000) reject("invalid stroke width");
    return;
  }
  if (name === "stroke-miterlimit") {
    if (!isPolicyNumber(value) || Number(value) < 1 || Number(value) > 1000) reject("invalid stroke miter limit");
    return;
  }
  if (name === "stroke-dasharray") {
    normalizeDashArray(value);
    return;
  }
  if (name === "stroke-linecap") {
    if (!["butt", "round", "square"].includes(value)) reject("invalid line cap");
    return;
  }
  if (name === "stroke-linejoin") {
    if (!["miter", "round", "bevel"].includes(value)) reject("invalid line join");
    return;
  }
  if (name === "font-family") {
    if (value !== "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif") reject("invalid font family");
    return;
  }
  if (name === "font-size") {
    if (!isPolicyNumber(value) || Number(value) < 8 || Number(value) > 96) reject("invalid font size");
    return;
  }
  if (name === "font-weight") {
    if (!["normal", "bold", "400", "500", "600", "700"].includes(value)) reject("invalid font weight");
    return;
  }
  if (name === "text-anchor") {
    if (!["start", "middle", "end"].includes(value)) reject("invalid text anchor");
    return;
  }
  if (name === "dominant-baseline") {
    if (!["auto", "central", "middle", "text-before-edge", "text-after-edge"].includes(value)) {
      reject("invalid dominant baseline");
    }
    return;
  }
  if (name === "transform") {
    normalizeTransform(value);
    return;
  }
  if (name === "points") {
    if (normalizePoints(value) !== value) reject("noncanonical point list");
    return;
  }
  if (name === "d") validatePath(value);
}

function validateAndReduceElement(element: Element): void {
  const name = element.localName;
  if (name === null || element.namespaceURI !== SVG_NAMESPACE || element.prefix !== null || !(name in ALLOWED_ATTRIBUTES)) {
    reject("unknown element or namespace");
  }
  for (const attribute of Array.from(element.attributes)) {
    if (attribute.name === "xmlns") {
      if (name !== "svg" || attribute.namespaceURI !== XMLNS_NAMESPACE || attribute.value !== SVG_NAMESPACE) {
        reject("invalid default namespace");
      }
      continue;
    }
    if (attribute.name === "xml:space" && attribute.prefix === "xml" &&
      attribute.namespaceURI === XML_NAMESPACE && TEXT_ELEMENTS.has(name) &&
      attribute.value === "preserve") continue;
    if (attribute.prefix !== null || attribute.namespaceURI !== null) reject("unknown attribute namespace");
    if (!ALLOWED_ATTRIBUTES[name]!.has(attribute.name) && !TRANSIENT_ATTRIBUTES.has(attribute.name)) {
      reject(`unknown attribute ${name}.${attribute.name}`);
    }
  }
  if (element.hasAttribute("class")) {
    const className = element.getAttribute("class") ?? "";
    if (!CLASS_NAME.test(className)) reject("unknown class");
  }
  if (element.hasAttribute("pointer-events") && !["visible", "none"].includes(element.getAttribute("pointer-events") ?? "")) {
    reject("unknown pointer-events value");
  }
  for (const name of ["ecmeta_series_index", "ecmeta_data_index"]) {
    if (element.hasAttribute(name) && !/^(?:0|[1-9][0-9]*)$/u.test(element.getAttribute(name) ?? "")) {
      reject("invalid ECharts metadata");
    }
  }
  if (element.hasAttribute("ecmeta_ssr_type") && !["chart", "legend"].includes(element.getAttribute("ecmeta_ssr_type") ?? "")) {
    reject("invalid ECharts metadata");
  }
  if (element.hasAttribute("ecmeta_silent") && element.getAttribute("ecmeta_silent") !== "true") {
    reject("invalid ECharts metadata");
  }
  materializeInlineStyle(element);
  reduceOpacity(element, "fill-opacity");
  reduceOpacity(element, "stroke-opacity");
  if (element.hasAttribute("transform")) {
    element.setAttribute("transform", normalizeTransform(element.getAttribute("transform") ?? ""));
  }
  if (element.hasAttribute("stroke-dasharray")) {
    element.setAttribute("stroke-dasharray", normalizeDashArray(element.getAttribute("stroke-dasharray") ?? ""));
  }
  if (element.hasAttribute("points")) {
    element.setAttribute("points", normalizePoints(element.getAttribute("points") ?? ""));
  }
  for (const transient of [
    "class", "pointer-events", "ecmeta_series_index", "ecmeta_data_index", "ecmeta_ssr_type", "ecmeta_silent"
  ]) element.removeAttribute(transient);
  for (const attribute of Array.from(element.attributes)) {
    if (attribute.name !== "xmlns" && !ALLOWED_ATTRIBUTES[name]!.has(attribute.name)) {
      reject("unreduced attribute");
    }
    if (["fill", "stroke", "clip-path"].includes(attribute.name) && /url\s*\(/iu.test(attribute.value)) {
      if (attribute.name !== "clip-path" || !/^url\(#[A-Za-z][A-Za-z0-9_-]{0,127}\)$/u.test(attribute.value)) {
        reject("external or obfuscated URL");
      }
    }
    if (!["xmlns", "id", "clip-path"].includes(attribute.name)) {
      validateFinalAttribute(attribute.name, attribute.value);
    }
  }
}

function validateDocumentNodes(node: Node, parentElement: Element | null = null): void {
  for (const child of Array.from(node.childNodes)) {
    if (child.nodeType === 1) {
      validateDocumentNodes(child, child as Element);
      continue;
    }
    if (child.nodeType === 3) {
      const text = child.nodeValue ?? "";
      if (parentElement === null) {
        if (text.trim() !== "") reject("text outside root");
      } else if (parentElement.localName === null) {
        reject("unnamed parent element");
      } else if (TEXT_ELEMENTS.has(parentElement.localName)) {
        if (text.normalize("NFC") !== text) reject("non-NFC text");
        if (/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F\u2028\u2029]/u.test(text)) {
          reject("forbidden text code point");
        }
      } else if (parentElement.localName === "style") {
        continue;
      } else if (!CONTAINER_ELEMENTS.has(parentElement.localName) || text.trim() !== "") {
        reject("unexpected text node");
      }
      continue;
    }
    if (child.nodeType === 4) reject("CDATA is forbidden");
    if (child.nodeType === 10) reject("doctype");
    reject("unknown XML node");
  }
}

function normalizeIds(elements: Element[]): void {
  const byOldId = new Map<string, Element>();
  const references: Array<{ element: Element; oldId: string }> = [];
  for (const element of elements) {
    if (element.hasAttribute("id")) {
      const oldId = element.getAttribute("id") ?? "";
      if (!ID_NAME.test(oldId) || byOldId.has(oldId)) reject("duplicate or invalid ID");
      byOldId.set(oldId, element);
    }
    if (element.hasAttribute("clip-path")) {
      const value = element.getAttribute("clip-path") ?? "";
      const match = /^url\(#([A-Za-z][A-Za-z0-9_-]{0,127})\)$/u.exec(value);
      if (match === null) reject("invalid internal reference");
      references.push({ element, oldId: match[1]! });
    }
  }
  for (const { oldId } of references) {
    if (!byOldId.has(oldId)) reject("unresolved internal reference");
  }
  const idMap = new Map<string, string>();
  let sequence = 0;
  for (const element of elements) {
    if (!element.hasAttribute("id")) continue;
    const oldId = element.getAttribute("id")!;
    const newId = `pa-svg-${sequence++}`;
    idMap.set(oldId, newId);
    element.setAttribute("id", newId);
  }
  for (const { element, oldId } of references) {
    element.setAttribute("clip-path", `url(#${idMap.get(oldId)!})`);
  }
}

function escapeText(value: string): string {
  return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function escapeAttribute(value: string): string {
  return escapeText(value).replaceAll('"', "&quot;").replaceAll("\t", "&#9;")
    .replaceAll("\n", "&#10;").replaceAll("\r", "&#13;");
}

function serializeElement(element: Element): string {
  const name = element.localName;
  if (name === null) reject("unnamed element");
  const attributes = Array.from(element.attributes).sort((left, right) => {
    if (left.name === "xmlns") return -1;
    if (right.name === "xmlns") return 1;
    return left.name < right.name ? -1 : left.name > right.name ? 1 : 0;
  });
  const start = `<${name}${attributes.map(({ name: attributeName, value }) =>
    ` ${attributeName}="${escapeAttribute(value)}"`).join("")}`;
  const children: string[] = [];
  for (const child of Array.from(element.childNodes)) {
    if (child.nodeType === 1) children.push(serializeElement(child as Element));
    else if (child.nodeType === 3) {
      const text = child.nodeValue ?? "";
      if (TEXT_ELEMENTS.has(name)) children.push(escapeText(text));
      else if (text.trim() !== "") reject("noncanonical container text");
    } else reject("unreduced XML node");
  }
  return children.length === 0 ? `${start}/>` : `${start}>${children.join("")}</${name}>`;
}

export function normalizeEChartsSvg(rawSvg: string): string {
  const document = parseXml(rawSvg);
  if (
    document.documentElement === null ||
    document.documentElement.localName !== "svg" ||
    document.documentElement.namespaceURI !== SVG_NAMESPACE
  ) reject("invalid root");
  enforceDocumentBudgets(document);
  validateDocumentNodes(document);
  const initialElements = elementsInDocumentOrder(document);
  const styles = initialElements.filter(({ localName }) => localName === "style");
  for (const style of styles) validateStyleSheet(style);
  for (const style of styles) style.parentNode?.removeChild(style);

  const root = document.documentElement;
  if (root.getAttribute("version") !== "1.1" || root.getAttribute("baseProfile") !== "full") {
    reject("unexpected SVG root metadata");
  }
  root.removeAttribute("version");
  root.removeAttribute("baseProfile");
  const xlink = root.getAttributeNode("xmlns:xlink");
  if (xlink !== null) {
    if (xlink.namespaceURI !== XMLNS_NAMESPACE || xlink.value !== XLINK_NAMESPACE) reject("invalid xlink namespace");
    root.removeAttributeNode(xlink);
  }

  const elements = elementsInDocumentOrder(document);
  for (const element of elements) validateAndReduceElement(element);
  normalizeIds(elements);
  return `${serializeElement(root)}\n`;
}
