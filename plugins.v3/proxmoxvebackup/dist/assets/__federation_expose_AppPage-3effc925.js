import { importShared } from './__federation_fn_import-054b33c3.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-c4c0bc37.js';

/**
 * Create a bound version of a function with a specified `this` context
 *
 * @param {Function} fn - The function to bind
 * @param {*} thisArg - The value to be passed as the `this` parameter
 * @returns {Function} A new function that will call the original function with the specified `this` context
 */
function bind(fn, thisArg) {
  return function wrap() {
    return fn.apply(thisArg, arguments);
  };
}

// utils is a library of generic helper functions non-specific to axios

const { toString } = Object.prototype;
const { getPrototypeOf } = Object;
const { iterator, toStringTag } = Symbol;

/* Creating a function that will check if an object has a property. */
const hasOwnProperty = (
  ({ hasOwnProperty }) =>
  (obj, prop) =>
    hasOwnProperty.call(obj, prop)
)(Object.prototype);

const isUnsafeObjectKey = (prop) =>
  typeof prop === 'string' &&
  (prop === '__proto__' || prop === 'constructor' || prop === 'prototype');

/**
 * Determine whether an inherited object must be treated as a shared-prototype
 * boundary. Cross-realm Object.prototype objects cannot be distinguished
 * reliably from application-created null-prototype objects because their
 * properties are mutable, so all inherited terminal prototypes are excluded
 * as a fail-closed boundary. A null-prototype source still keeps its own
 * properties, as produced by mergeConfig and other safe materialization paths.
 *
 * @param {*} obj The object to inspect
 * @param {*} prototype The object's prototype
 * @param {boolean} source Whether obj is the original traversal source
 *
 * @returns {boolean} True when obj is a safe prototype traversal boundary
 */
const isPrototypeBoundary = (obj, prototype, source) =>
  obj === Object.prototype || (!source && prototype === null);

/**
 * Determine whether an object can retain its identity through code paths that
 * add, replace, and remove config properties without bypassing unsafe-key
 * filtering. Immutable objects, unsafe-key-bearing objects, and objects with
 * accessor or restricted data properties must be materialized instead.
 *
 * @param {*} obj The object to inspect
 *
 * @returns {boolean} True when every own property is safe and fully mutable
 */
const isSafeAndFullyMutable = (obj) => {
  if (!Object.isExtensible(obj)) {
    return false;
  }

  const props = Object.getOwnPropertyNames(obj);

  if (Object.getOwnPropertySymbols) {
    props.push(...Object.getOwnPropertySymbols(obj));
  }

  return props.every((prop) => {
    if (isUnsafeObjectKey(prop)) {
      return false;
    }

    const descriptor = Object.getOwnPropertyDescriptor(obj, prop);

    return !!descriptor && descriptor.configurable && descriptor.writable === true;
  });
};

/**
 * Walk the prototype chain (excluding the source realm's Object.prototype)
 * looking for an own `prop`. This distinguishes genuine own/inherited members
 * — including class accessors and template prototypes — from members injected
 * via Object.prototype pollution (e.g. `Object.prototype.username = '...'`),
 * which live on Object.prototype itself and are therefore never matched.
 *
 * @param {*} thing The value whose chain to inspect
 * @param {string|symbol} prop The property key to look for
 *
 * @returns {boolean} True when `prop` is owned below Object.prototype
 */
const hasOwnInPrototypeChain = (thing, prop) => {
  let obj = thing;
  const seen = [];

  while (obj != null) {
    if (seen.indexOf(obj) !== -1) {
      return false;
    }
    seen.push(obj);

    const prototype = getPrototypeOf(obj);

    if (isPrototypeBoundary(obj, prototype, obj === thing)) {
      return false;
    }

    if (hasOwnProperty(obj, prop)) {
      return true;
    }
    obj = prototype;
  }
  return false;
};

/**
 * Read `obj[prop]` only when it is safe from Object.prototype pollution. Own
 * properties and members inherited from a non-Object.prototype source (a class
 * instance or template object) are honored; a value reachable only through a
 * polluted Object.prototype is ignored and `undefined` is returned.
 *
 * @param {*} obj The source object
 * @param {string|symbol} prop The property key to read
 *
 * @returns {*} The resolved value, or undefined when unsafe/absent
 */
const getSafeProp = (obj, prop) =>
  obj != null && hasOwnInPrototypeChain(obj, prop) ? obj[prop] : undefined;

/**
 * Flatten an object and its application-defined prototype chain into a
 * null-prototype object. Members inherited only from the source realm's
 * Object.prototype are deliberately excluded, while class/template members
 * below that boundary are preserved.
 *
 * @param {*} thing The value to flatten
 *
 * @returns {*} A null-prototype copy, or the original value when it is already
 * structurally safe or is not an object
 */
const toSafeFlatObject = (thing) => {
  if (thing == null || (typeof thing !== 'object' && typeof thing !== 'function')) {
    return thing;
  }

  const sourcePrototype = getPrototypeOf(thing);

  if (sourcePrototype === null && isSafeAndFullyMutable(thing)) {
    return thing;
  }

  const result = Object.create(null);
  const merged = Object.create(null);
  const seen = [];
  let current = thing;

  while (current != null) {
    if (seen.indexOf(current) !== -1) {
      break;
    }

    seen.push(current);

    const prototype = current === thing ? sourcePrototype : getPrototypeOf(current);

    if (isPrototypeBoundary(current, prototype, current === thing)) {
      break;
    }

    const props = Object.getOwnPropertyNames(current);

    if (Object.getOwnPropertySymbols) {
      props.push(...Object.getOwnPropertySymbols(current));
    }

    for (const prop of props) {
      if (isUnsafeObjectKey(prop)) {
        continue;
      }

      if (!hasOwnProperty(merged, prop)) {
        result[prop] = thing[prop];
        merged[prop] = true;
      }
    }

    current = prototype;
  }

  return result;
};

const kindOf = ((cache) => (thing) => {
  const str = toString.call(thing);
  return cache[str] || (cache[str] = str.slice(8, -1).toLowerCase());
})(Object.create(null));

const kindOfTest = (type) => {
  type = type.toLowerCase();
  return (thing) => kindOf(thing) === type;
};

const typeOfTest = (type) => (thing) => typeof thing === type;

/**
 * Determine if a value is a non-null object
 *
 * @param {Object} val The value to test
 *
 * @returns {boolean} True if value is an Array, otherwise false
 */
const { isArray } = Array;

/**
 * Determine if a value is undefined
 *
 * @param {*} val The value to test
 *
 * @returns {boolean} True if the value is undefined, otherwise false
 */
const isUndefined = typeOfTest('undefined');

/**
 * Determine if a value is a Buffer
 *
 * @param {*} val The value to test
 *
 * @returns {boolean} True if value is a Buffer, otherwise false
 */
function isBuffer(val) {
  return (
    val !== null &&
    !isUndefined(val) &&
    val.constructor !== null &&
    !isUndefined(val.constructor) &&
    isFunction$1(val.constructor.isBuffer) &&
    val.constructor.isBuffer(val)
  );
}

/**
 * Determine if a value is an ArrayBuffer
 *
 * @param {*} val The value to test
 *
 * @returns {boolean} True if value is an ArrayBuffer, otherwise false
 */
const isArrayBuffer = kindOfTest('ArrayBuffer');

/**
 * Determine if a value is a view on an ArrayBuffer
 *
 * @param {*} val The value to test
 *
 * @returns {boolean} True if value is a view on an ArrayBuffer, otherwise false
 */
function isArrayBufferView(val) {
  let result;
  if (typeof ArrayBuffer !== 'undefined' && ArrayBuffer.isView) {
    result = ArrayBuffer.isView(val);
  } else {
    result = val && val.buffer && isArrayBuffer(val.buffer);
  }
  return result;
}

/**
 * Determine if a value is a String
 *
 * @param {*} val The value to test
 *
 * @returns {boolean} True if value is a String, otherwise false
 */
const isString = typeOfTest('string');

/**
 * Determine if a value is a Function
 *
 * @param {*} val The value to test
 * @returns {boolean} True if value is a Function, otherwise false
 */
const isFunction$1 = typeOfTest('function');

/**
 * Determine if a value is a Number
 *
 * @param {*} val The value to test
 *
 * @returns {boolean} True if value is a Number, otherwise false
 */
const isNumber = typeOfTest('number');

/**
 * Determine if a value is an Object
 *
 * @param {*} thing The value to test
 *
 * @returns {boolean} True if value is an Object, otherwise false
 */
const isObject = (thing) => thing !== null && typeof thing === 'object';

/**
 * Determine if a value is a Boolean
 *
 * @param {*} thing The value to test
 * @returns {boolean} True if value is a Boolean, otherwise false
 */
const isBoolean = (thing) => thing === true || thing === false;

/**
 * Determine if a value is a plain Object
 *
 * @param {*} val The value to test
 *
 * @returns {boolean} True if value is a plain Object, otherwise false
 */
const isPlainObject = (val) => {
  if (!isObject(val)) {
    return false;
  }

  const prototype = getPrototypeOf(val);
  return (
    (prototype === null || prototype === Object.prototype || getPrototypeOf(prototype) === null) &&
    // Treat own Symbol.toStringTag or Symbol.iterator members as evidence the
    // value is tagged/iterable, ignoring members reachable only through shared
    // or terminal prototype boundaries. This is exactly what
    // hasOwnInPrototypeChain(val, prop) computes here: every prototype admitted
    // above (null, Object.prototype, or a terminal null-prototype template) is
    // a boundary, so the walk never inspects anything but `val`'s own members,
    // and stops before even those when `val` is itself the boundary
    // Object.prototype. Checking that inline avoids allocating the walker's
    // `seen` list twice per call on the mergeConfig / merge hot path.
    (isPrototypeBoundary(val, prototype, true) ||
      (!hasOwnProperty(val, toStringTag) && !hasOwnProperty(val, iterator)))
  );
};

/**
 * Determine if a value is an empty object (safely handles Buffers)
 *
 * @param {*} val The value to test
 *
 * @returns {boolean} True if value is an empty object, otherwise false
 */
const isEmptyObject = (val) => {
  // Early return for non-objects or Buffers to prevent RangeError
  if (!isObject(val) || isBuffer(val)) {
    return false;
  }

  try {
    return Object.keys(val).length === 0 && Object.getPrototypeOf(val) === Object.prototype;
  } catch (e) {
    // Fallback for any other objects that might cause RangeError with Object.keys()
    return false;
  }
};

/**
 * Determine if a value is a Date
 *
 * @param {*} val The value to test
 *
 * @returns {boolean} True if value is a Date, otherwise false
 */
const isDate = kindOfTest('Date');

/**
 * Determine if a value is a File
 *
 * @param {*} val The value to test
 *
 * @returns {boolean} True if value is a File, otherwise false
 */
const isFile = kindOfTest('File');

/**
 * Determine if a value is a React Native Blob
 * React Native "blob": an object with a `uri` attribute. Optionally, it can
 * also have a `name` and `type` attribute to specify filename and content type
 *
 * @see https://github.com/facebook/react-native/blob/26684cf3adf4094eb6c405d345a75bf8c7c0bf88/Libraries/Network/FormData.js#L68-L71
 *
 * @param {*} value The value to test
 *
 * @returns {boolean} True if value is a React Native Blob, otherwise false
 */
const isReactNativeBlob = (value) => {
  return !!(value && typeof value.uri !== 'undefined');
};

/**
 * Determine if environment is React Native
 * ReactNative `FormData` has a non-standard `getParts()` method
 *
 * @param {*} formData The formData to test
 *
 * @returns {boolean} True if environment is React Native, otherwise false
 */
const isReactNative = (formData) => formData && typeof formData.getParts !== 'undefined';

/**
 * Determine if a value is a Blob
 *
 * @param {*} val The value to test
 *
 * @returns {boolean} True if value is a Blob, otherwise false
 */
const isBlob = kindOfTest('Blob');

/**
 * Determine if a value is a FileList
 *
 * @param {*} val The value to test
 *
 * @returns {boolean} True if value is a FileList, otherwise false
 */
const isFileList = kindOfTest('FileList');
const isSet = kindOfTest('Set');

/**
 * Determine if a value is a Stream
 *
 * @param {*} val The value to test
 *
 * @returns {boolean} True if value is a Stream, otherwise false
 */
const isStream = (val) => isObject(val) && isFunction$1(val.pipe);

/**
 * Determine if a value is a FormData
 *
 * @param {*} thing The value to test
 *
 * @returns {boolean} True if value is an FormData, otherwise false
 */
function getGlobal() {
  if (typeof globalThis !== 'undefined') return globalThis;
  if (typeof self !== 'undefined') return self;
  if (typeof window !== 'undefined') return window;
  if (typeof global !== 'undefined') return global;
  return {};
}

const G = getGlobal();
const FormDataCtor = typeof G.FormData !== 'undefined' ? G.FormData : undefined;

const isFormData = (thing) => {
  if (!thing) return false;
  if (FormDataCtor && thing instanceof FormDataCtor) return true;
  // Reject plain objects inheriting directly from Object.prototype so prototype-pollution gadgets can't spoof FormData.
  const proto = getPrototypeOf(thing);
  if (!proto || proto === Object.prototype) return false;
  if (!isFunction$1(thing.append)) return false;
  const kind = kindOf(thing);
  return (
    kind === 'formdata' ||
    // detect form-data instance
    (kind === 'object' && isFunction$1(thing.toString) && thing.toString() === '[object FormData]')
  );
};

/**
 * Determine if a value is a URLSearchParams object
 *
 * @param {*} val The value to test
 *
 * @returns {boolean} True if value is a URLSearchParams object, otherwise false
 */
const isURLSearchParams = kindOfTest('URLSearchParams');

const [isReadableStream, isRequest, isResponse, isHeaders] = [
  'ReadableStream',
  'Request',
  'Response',
  'Headers',
].map(kindOfTest);

/**
 * Trim excess whitespace off the beginning and end of a string
 *
 * @param {String} str The String to trim
 *
 * @returns {String} The String freed of excess whitespace
 */
const trim = (str) => {
  return str.trim ? str.trim() : str.replace(/^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g, '');
};
/**
 * Iterate over an Array or an Object invoking a function for each item.
 *
 * If `obj` is an Array callback will be called passing
 * the value, index, and complete array for each item.
 *
 * If 'obj' is an Object callback will be called passing
 * the value, key, and complete object for each property.
 *
 * @param {Object|Array<unknown>} obj The object to iterate
 * @param {Function} fn The callback to invoke for each item
 *
 * @param {Object} [options]
 * @param {Boolean} [options.allOwnKeys = false]
 * @returns {any}
 */
function forEach(obj, fn, { allOwnKeys = false } = {}) {
  // Don't bother if no value provided
  if (obj === null || typeof obj === 'undefined') {
    return;
  }

  let i;
  let l;

  // Force an array if not already something iterable
  if (typeof obj !== 'object') {
    /*eslint no-param-reassign:0*/
    obj = [obj];
  }

  if (isArray(obj)) {
    // Iterate over array values
    for (i = 0, l = obj.length; i < l; i++) {
      fn.call(null, obj[i], i, obj);
    }
  } else {
    // Buffer check
    if (isBuffer(obj)) {
      return;
    }

    // Iterate over object keys
    const keys = allOwnKeys ? Object.getOwnPropertyNames(obj) : Object.keys(obj);
    const len = keys.length;
    let key;

    for (i = 0; i < len; i++) {
      key = keys[i];
      fn.call(null, obj[key], key, obj);
    }
  }
}

/**
 * Finds a key in an object, case-insensitive, returning the actual key name.
 * Returns null if the object is a Buffer or if no match is found.
 *
 * @param {Object} obj - The object to search.
 * @param {string} key - The key to find (case-insensitive).
 * @returns {?string} The actual key name if found, otherwise null.
 */
function findKey(obj, key) {
  if (isBuffer(obj)) {
    return null;
  }

  key = key.toLowerCase();
  const keys = Object.keys(obj);
  let i = keys.length;
  let _key;
  while (i-- > 0) {
    _key = keys[i];
    if (key === _key.toLowerCase()) {
      return _key;
    }
  }
  return null;
}

const _global = (() => {
  /*eslint no-undef:0*/
  if (typeof globalThis !== 'undefined') return globalThis;
  return typeof self !== 'undefined' ? self : typeof window !== 'undefined' ? window : global;
})();

const isContextDefined = (context) => !isUndefined(context) && context !== _global;

/**
 * Accepts varargs expecting each argument to be an object, then
 * immutably merges the properties of each object and returns result.
 *
 * When multiple objects contain the same key the later object in
 * the arguments list will take precedence.
 *
 * Example:
 *
 * ```js
 * const result = merge({foo: 123}, {foo: 456});
 * console.log(result.foo); // outputs 456
 * ```
 *
 * @param {Object} obj1 Object to merge
 *
 * @returns {Object} Result of all merge properties
 */
function merge(...objs) {
  const { caseless, skipUndefined } = (isContextDefined(this) && this) || {};
  const result = {};
  // Caseless lookup only applies to string keys — symbol keys are
  // identity-matched. Every string key that reaches `result` passes through
  // this index first, so it can never hold two case variants of one key and a
  // lowercase -> key map is exactly what findKey(result, key) would rescan
  // Object.keys(result) for on each assignment.
  const lowerCaseKeys = caseless ? Object.create(null) : null;
  const assignValue = (val, key) => {
    // Skip dangerous property names to prevent prototype pollution
    if (key === '__proto__' || key === 'constructor' || key === 'prototype') {
      return;
    }

    let targetKey = key;
    if (lowerCaseKeys && typeof key === 'string') {
      const lowerKey = key.toLowerCase();
      const knownKey = lowerCaseKeys[lowerKey];
      // A key recorded but absent from `result` was skipped by skipUndefined;
      // the later spelling wins then, as it does for findKey.
      if (knownKey !== undefined && hasOwnProperty(result, knownKey)) {
        targetKey = knownKey;
      } else {
        lowerCaseKeys[lowerKey] = key;
      }
    }
    // Read via own-prop only — a bare `result[targetKey]` walks the prototype
    // chain, so a polluted Object.prototype value could surface here and get
    // copied into the merged result.
    const existing = hasOwnProperty(result, targetKey) ? result[targetKey] : undefined;
    if (isPlainObject(existing) && isPlainObject(val)) {
      result[targetKey] = merge(existing, val);
    } else if (isPlainObject(val)) {
      result[targetKey] = merge({}, val);
    } else if (isArray(val)) {
      result[targetKey] = val.slice();
    } else if (!skipUndefined || !isUndefined(val)) {
      result[targetKey] = val;
    }
  };

  for (let i = 0, l = objs.length; i < l; i++) {
    const source = objs[i];
    if (!source || isBuffer(source)) {
      continue;
    }

    forEach(source, assignValue);

    if (typeof source !== 'object' || isArray(source) || !Object.getOwnPropertySymbols) {
      continue;
    }

    const symbols = Object.getOwnPropertySymbols(source);
    for (let j = 0; j < symbols.length; j++) {
      const symbol = symbols[j];
      if (propertyIsEnumerable.call(source, symbol)) {
        assignValue(source[symbol], symbol);
      }
    }
  }
  return result;
}

/**
 * Extends object a by mutably adding to it the properties of object b.
 *
 * @param {Object} a The object to be extended
 * @param {Object} b The object to copy properties from
 * @param {Object} thisArg The object to bind function to
 *
 * @param {Object} [options]
 * @param {Boolean} [options.allOwnKeys]
 * @returns {Object} The resulting value of object a
 */
const extend = (a, b, thisArg, { allOwnKeys } = {}) => {
  forEach(
    b,
    (val, key) => {
      if (thisArg && isFunction$1(val)) {
        Object.defineProperty(a, key, {
          // Null-proto descriptor so a polluted Object.prototype.get cannot
          // hijack defineProperty's accessor-vs-data resolution.
          __proto__: null,
          value: bind(val, thisArg),
          writable: true,
          enumerable: true,
          configurable: true,
        });
      } else {
        Object.defineProperty(a, key, {
          __proto__: null,
          value: val,
          writable: true,
          enumerable: true,
          configurable: true,
        });
      }
    },
    { allOwnKeys }
  );
  return a;
};

/**
 * Remove byte order marker. This catches EF BB BF (the UTF-8 BOM)
 *
 * @param {string} content with BOM
 *
 * @returns {string} content value without BOM
 */
const stripBOM = (content) => {
  if (content.charCodeAt(0) === 0xfeff) {
    content = content.slice(1);
  }
  return content;
};

/**
 * Inherit the prototype methods from one constructor into another
 * @param {function} constructor
 * @param {function} superConstructor
 * @param {object} [props]
 * @param {object} [descriptors]
 *
 * @returns {void}
 */
const inherits = (constructor, superConstructor, props, descriptors) => {
  constructor.prototype = Object.create(superConstructor.prototype, descriptors);
  Object.defineProperty(constructor.prototype, 'constructor', {
    __proto__: null,
    value: constructor,
    writable: true,
    enumerable: false,
    configurable: true,
  });
  Object.defineProperty(constructor, 'super', {
    __proto__: null,
    value: superConstructor.prototype,
  });
  props && Object.assign(constructor.prototype, props);
};

/**
 * Resolve object with deep prototype chain to a flat object
 * @param {Object} sourceObj source object
 * @param {Object} [destObj]
 * @param {Function|Boolean} [filter]
 * @param {Function} [propFilter]
 *
 * @returns {Object}
 */
const toFlatObject = (sourceObj, destObj, filter, propFilter) => {
  let props;
  let i;
  let prop;
  const merged = {};

  destObj = destObj || {};
  // eslint-disable-next-line no-eq-null,eqeqeq
  if (sourceObj == null) return destObj;

  do {
    props = Object.getOwnPropertyNames(sourceObj);
    i = props.length;
    while (i-- > 0) {
      prop = props[i];
      if ((!propFilter || propFilter(prop, sourceObj, destObj)) && !merged[prop]) {
        destObj[prop] = sourceObj[prop];
        merged[prop] = true;
      }
    }
    sourceObj = filter !== false && getPrototypeOf(sourceObj);
  } while (sourceObj && (!filter || filter(sourceObj, destObj)) && sourceObj !== Object.prototype);

  return destObj;
};

/**
 * Determines whether a string ends with the characters of a specified string
 *
 * @param {String} str
 * @param {String} searchString
 * @param {Number} [position= 0]
 *
 * @returns {boolean}
 */
const endsWith = (str, searchString, position) => {
  str = String(str);
  if (position === undefined || position > str.length) {
    position = str.length;
  }
  position -= searchString.length;
  const lastIndex = str.indexOf(searchString, position);
  return lastIndex !== -1 && lastIndex === position;
};

/**
 * Returns new array from array like object or null if failed
 *
 * @param {*} [thing]
 *
 * @returns {?Array}
 */
const toArray = (thing) => {
  if (!thing) return null;
  if (isArray(thing)) return thing;
  let i = thing.length;
  if (!Number.isSafeInteger(i) || i < 0 || i > 0xffffffff) return null;

  // Bound the copy by actual indexed properties, including hidden and inherited
  // members of array-like collections, rather than by the declared length alone.
  const indexes = new Set();
  const seen = new Set();
  let source = thing;

  while (source != null && indexes.size < i) {
    if (seen.has(source)) return null;
    seen.add(source);

    const prototype = getPrototypeOf(source);
    if (isPrototypeBoundary(source, prototype, source === thing)) break;

    Object.getOwnPropertyNames(source).forEach((key) => {
      const index = +key;
      if (
        Number.isInteger(index) &&
        index >= 0 &&
        index < i &&
        String(index) === key &&
        hasOwnProperty(source, key)
      ) {
        indexes.add(index);
      }
    });
    source = prototype;
  }

  if (indexes.size !== i) return null;
  const arr = new Array(i);
  while (i-- > 0) {
    arr[i] = thing[i];
  }
  return arr;
};

/**
 * Checking if the Uint8Array exists and if it does, it returns a function that checks if the
 * thing passed in is an instance of Uint8Array
 *
 * @param {TypedArray}
 *
 * @returns {Array}
 */
// eslint-disable-next-line func-names
const isTypedArray = ((TypedArray) => {
  // eslint-disable-next-line func-names
  return (thing) => {
    return TypedArray && thing instanceof TypedArray;
  };
})(typeof Uint8Array !== 'undefined' && getPrototypeOf(Uint8Array));

/**
 * For each entry in the object, call the function with the key and value.
 *
 * @param {Object<any, any>} obj - The object to iterate over.
 * @param {Function} fn - The function to call for each entry.
 *
 * @returns {void}
 */
const forEachEntry = (obj, fn) => {
  const generator = obj && obj[iterator];

  const _iterator = generator.call(obj);

  let result;

  while ((result = _iterator.next()) && !result.done) {
    const pair = result.value;
    fn.call(obj, pair[0], pair[1]);
  }
};

/**
 * It takes a regular expression and a string, and returns an array of all the matches
 *
 * @param {string} regExp - The regular expression to match against.
 * @param {string} str - The string to search.
 *
 * @returns {Array<boolean>}
 */
const matchAll = (regExp, str) => {
  let matches;
  const arr = [];

  while ((matches = regExp.exec(str)) !== null) {
    arr.push(matches);
  }

  return arr;
};

/* Checking if the kindOfTest function returns true when passed an HTMLFormElement. */
const isHTMLForm = kindOfTest('HTMLFormElement');

const toCamelCase = (str) => {
  return str.toLowerCase().replace(/[-_\s]([a-z\d])(\w*)/g, function replacer(m, p1, p2) {
    return p1.toUpperCase() + p2;
  });
};

const { propertyIsEnumerable } = Object.prototype;

/**
 * Determine if a value is a RegExp object
 *
 * @param {*} val The value to test
 *
 * @returns {boolean} True if value is a RegExp object, otherwise false
 */
const isRegExp = kindOfTest('RegExp');

const reduceDescriptors = (obj, reducer) => {
  const descriptors = Object.getOwnPropertyDescriptors(obj);
  const reducedDescriptors = {};

  forEach(descriptors, (descriptor, name) => {
    let ret;
    if ((ret = reducer(descriptor, name, obj)) !== false) {
      reducedDescriptors[name] = ret || descriptor;
    }
  });

  Object.defineProperties(obj, reducedDescriptors);
};

/**
 * Makes all methods read-only
 * @param {Object} obj
 */

const freezeMethods = (obj) => {
  reduceDescriptors(obj, (descriptor, name) => {
    // skip restricted props in strict mode
    if (isFunction$1(obj) && ['arguments', 'caller', 'callee'].includes(name)) {
      return false;
    }

    const value = obj[name];

    if (!isFunction$1(value)) return;

    descriptor.enumerable = false;

    if ('writable' in descriptor) {
      descriptor.writable = false;
      return;
    }

    if (!descriptor.set) {
      descriptor.set = () => {
        throw Error("Can not rewrite read-only method '" + name + "'");
      };
    }
  });
};

/**
 * Converts an array or a delimited string into an object set with values as keys and true as values.
 * Useful for fast membership checks.
 *
 * @param {Array|string} arrayOrString - The array or string to convert.
 * @param {string} delimiter - The delimiter to use if input is a string.
 * @returns {Object} An object with keys from the array or string, values set to true.
 */
const toObjectSet = (arrayOrString, delimiter) => {
  const obj = {};

  const define = (arr) => {
    arr.forEach((value) => {
      obj[value] = true;
    });
  };

  isArray(arrayOrString) ? define(arrayOrString) : define(String(arrayOrString).split(delimiter));

  return obj;
};

const noop = () => {};

const toFiniteNumber = (value, defaultValue) => {
  return value != null && Number.isFinite((value = +value)) ? value : defaultValue;
};

/**
 * If the thing is a FormData object, return true, otherwise return false.
 *
 * @param {unknown} thing - The thing to check.
 *
 * @returns {boolean}
 */
function isSpecCompliantForm(thing) {
  return !!(
    thing &&
    isFunction$1(thing.append) &&
    thing[toStringTag] === 'FormData' &&
    thing[iterator]
  );
}

/**
 * Recursively converts an object to a JSON-compatible object, handling circular references and Buffers.
 *
 * @param {Object} obj - The object to convert.
 * @returns {Object} The JSON-compatible object.
 */
const toJSONObject = (obj) => {
  const visited = new WeakSet();

  const visit = (source) => {
    if (isObject(source)) {
      if (visited.has(source)) {
        return;
      }

      //Buffer check
      if (isBuffer(source)) {
        return source;
      }

      if (!('toJSON' in source)) {
        // add-on descent / delete-on-ascent: preserves path semantics, so DAG nodes serialise at every occurrence (see #7230).
        visited.add(source);

        let target;

        if (isSet(source)) {
          target = [];
          for (const value of source) {
            const reducedValue = visit(value);
            !isUndefined(reducedValue) && target.push(reducedValue);
          }
        } else {
          target = isArray(source) ? [] : {};

          forEach(source, (value, key) => {
            const reducedValue = visit(value);
            !isUndefined(reducedValue) && (target[key] = reducedValue);
          });
        }

        visited.delete(source);

        return target;
      }
    }

    return source;
  };

  return visit(obj);
};

/**
 * Determines if a value is an async function.
 *
 * @param {*} thing - The value to test.
 * @returns {boolean} True if value is an async function, otherwise false.
 */
const isAsyncFn = kindOfTest('AsyncFunction');

/**
 * Determines if a value is thenable (has then and catch methods).
 *
 * @param {*} thing - The value to test.
 * @returns {boolean} True if value is thenable, otherwise false.
 */
const isThenable = (thing) =>
  thing &&
  (isObject(thing) || isFunction$1(thing)) &&
  isFunction$1(thing.then) &&
  isFunction$1(thing.catch);

// original code
// https://github.com/DigitalBrainJS/AxiosPromise/blob/16deab13710ec09779922131f3fa5954320f83ab/lib/utils.js#L11-L34

/**
 * Provides a cross-platform setImmediate implementation.
 * Uses native setImmediate if available, otherwise falls back to postMessage or setTimeout.
 *
 * @param {boolean} setImmediateSupported - Whether setImmediate is supported.
 * @param {boolean} postMessageSupported - Whether postMessage is supported.
 * @returns {Function} A function to schedule a callback asynchronously.
 */
const _setImmediate = ((setImmediateSupported, postMessageSupported) => {
  if (setImmediateSupported) {
    return setImmediate;
  }

  return postMessageSupported
    ? ((token, callbacks) => {
        _global.addEventListener(
          'message',
          ({ source, data }) => {
            if (source === _global && data === token) {
              callbacks.length && callbacks.shift()();
            }
          },
          false
        );

        return (cb) => {
          callbacks.push(cb);
          _global.postMessage(token, '*');
        };
      })(`axios@${Math.random()}`, [])
    : (cb) => setTimeout(cb);
})(typeof setImmediate === 'function', isFunction$1(_global.postMessage));

/**
 * Schedules a microtask or asynchronous callback as soon as possible.
 * Uses queueMicrotask if available, otherwise falls back to process.nextTick or _setImmediate.
 *
 * @type {Function}
 */
const asap =
  typeof queueMicrotask !== 'undefined'
    ? queueMicrotask.bind(_global)
    : (typeof process !== 'undefined' && process.nextTick) || _setImmediate;

// *********************

const isIterable = (thing) => thing != null && isFunction$1(thing[iterator]);

/**
 * Determine if a value is iterable via an iterator that is NOT sourced solely
 * from a polluted Object.prototype. Use this instead of `isIterable` whenever
 * the iterable comes from untrusted input (e.g. user-supplied header sources),
 * so `Object.prototype[Symbol.iterator] = ...` cannot turn an ordinary object
 * into an attacker-controlled entries iterator.
 *
 * @param {*} thing The value to test
 *
 * @returns {boolean} True if value has a non-polluted iterator
 */
const isSafeIterable = (thing) =>
  thing != null && hasOwnInPrototypeChain(thing, iterator) && isIterable(thing);

const utils$1 = {
  isArray,
  isArrayBuffer,
  isBuffer,
  isFormData,
  isArrayBufferView,
  isString,
  isNumber,
  isBoolean,
  isObject,
  isPlainObject,
  isEmptyObject,
  isReadableStream,
  isRequest,
  isResponse,
  isHeaders,
  isUndefined,
  isDate,
  isFile,
  isReactNativeBlob,
  isReactNative,
  isBlob,
  isRegExp,
  isFunction: isFunction$1,
  isStream,
  isURLSearchParams,
  isTypedArray,
  isFileList,
  forEach,
  merge,
  extend,
  trim,
  stripBOM,
  inherits,
  toFlatObject,
  kindOf,
  kindOfTest,
  endsWith,
  toArray,
  forEachEntry,
  matchAll,
  isHTMLForm,
  hasOwnProperty,
  hasOwnProp: hasOwnProperty, // an alias to avoid ESLint no-prototype-builtins detection
  hasOwnInPrototypeChain,
  getSafeProp,
  toSafeFlatObject,
  reduceDescriptors,
  freezeMethods,
  toObjectSet,
  toCamelCase,
  noop,
  toFiniteNumber,
  findKey,
  global: _global,
  isContextDefined,
  isSpecCompliantForm,
  toJSONObject,
  isAsyncFn,
  isThenable,
  setImmediate: _setImmediate,
  asap,
  isIterable,
  isSafeIterable,
};

// RawAxiosHeaders whose duplicates are ignored by node
// c.f. https://nodejs.org/api/http.html#http_message_headers
const ignoreDuplicateOf = utils$1.toObjectSet([
  'age',
  'authorization',
  'content-length',
  'content-type',
  'etag',
  'expires',
  'from',
  'host',
  'if-modified-since',
  'if-unmodified-since',
  'last-modified',
  'location',
  'max-forwards',
  'proxy-authorization',
  'referer',
  'retry-after',
  'user-agent',
]);

/**
 * Parse headers into an object
 *
 * ```
 * Date: Wed, 27 Aug 2014 08:58:49 GMT
 * Content-Type: application/json
 * Connection: keep-alive
 * Transfer-Encoding: chunked
 * ```
 *
 * @param {String} rawHeaders Headers needing to be parsed
 *
 * @returns {Object} Headers parsed into an object
 */
const parseHeaders = (rawHeaders) => {
  // Header names are data, including __proto__; avoid inherited setters.
  const parsed = Object.create(null);
  let key;
  let val;
  let i;

  rawHeaders &&
    rawHeaders.split('\n').forEach(function parser(line) {
      i = line.indexOf(':');
      key = line.substring(0, i).trim().toLowerCase();
      val = line.substring(i + 1).trim();

      const hasKey = utils$1.hasOwnProp(parsed, key);

      if (!key || (hasKey && utils$1.hasOwnProp(ignoreDuplicateOf, key))) {
        return;
      }

      if (key === 'set-cookie') {
        if (hasKey) {
          parsed[key].push(val);
        } else {
          parsed[key] = [val];
        }
      } else {
        parsed[key] = hasKey ? parsed[key] + ', ' + val : val;
      }
    });

  return parsed;
};

function trimSPorHTAB(str) {
  let start = 0;
  let end = str.length;

  while (start < end) {
    const code = str.charCodeAt(start);

    if (code !== 0x09 && code !== 0x20) {
      break;
    }

    start += 1;
  }

  while (end > start) {
    const code = str.charCodeAt(end - 1);

    if (code !== 0x09 && code !== 0x20) {
      break;
    }

    end -= 1;
  }

  return start === 0 && end === str.length ? str : str.slice(start, end);
}

// The control-code ranges are intentional: header sanitization strips C0/DEL bytes.
// eslint-disable-next-line no-control-regex
const INVALID_UNICODE_HEADER_VALUE_CHARS = new RegExp('[\\u0000-\\u0008\\u000a-\\u001f\\u007f]+', 'g');
// eslint-disable-next-line no-control-regex
const INVALID_BYTE_STRING_HEADER_VALUE_CHARS = new RegExp('[^\\u0009\\u0020-\\u007e\\u0080-\\u00ff]+', 'g');

function sanitizeValue(value, invalidChars) {
  if (utils$1.isArray(value)) {
    return value.map((item) => sanitizeValue(item, invalidChars));
  }

  return trimSPorHTAB(String(value).replace(invalidChars, ''));
}

const sanitizeHeaderValue = (value) =>
  sanitizeValue(value, INVALID_UNICODE_HEADER_VALUE_CHARS);

const sanitizeByteStringHeaderValue = (value) =>
  sanitizeValue(value, INVALID_BYTE_STRING_HEADER_VALUE_CHARS);

function toByteStringHeaderObject(headers) {
  const byteStringHeaders = Object.create(null);

  utils$1.forEach(headers.toJSON(), (value, header) => {
    byteStringHeaders[header] = sanitizeByteStringHeaderValue(value);
  });

  return byteStringHeaders;
}

const $internals$1 = Symbol('internals');

function normalizeHeader(header) {
  return header && String(header).trim().toLowerCase();
}

function normalizeValue(value) {
  if (value === false || value == null) {
    return value;
  }

  return utils$1.isArray(value) ? value.map(normalizeValue) : sanitizeHeaderValue(String(value));
}

function parseTokens(str) {
  const tokens = Object.create(null);
  const tokensRE = /([^\s,;=]+)\s*(?:=\s*([^,;]+))?/g;
  let match;

  while ((match = tokensRE.exec(str))) {
    tokens[match[1]] = match[2];
  }

  return tokens;
}

const parameterNameRE = /^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$/;

function trimOWS(value) {
  let start = 0;
  let end = value.length;

  while (start < end) {
    const code = value.charCodeAt(start);

    if (code !== 0x09 && code !== 0x20) {
      break;
    }

    start += 1;
  }

  while (end > start) {
    const code = value.charCodeAt(end - 1);

    if (code !== 0x09 && code !== 0x20) {
      break;
    }

    end -= 1;
  }

  return start === 0 && end === value.length ? value : value.slice(start, end);
}

function decodeQuotedString(value) {
  const last = value.length - 1;

  if (last < 1 || value.charCodeAt(0) !== 0x22 || value.charCodeAt(last) !== 0x22) {
    return value;
  }

  let decoded = '';

  for (let i = 1; i < last; i++) {
    const code = value.charCodeAt(i);

    if (code === 0x22) {
      return value;
    }

    if (code === 0x5c) {
      i += 1;

      if (i >= last) {
        return value;
      }
    }

    decoded += value[i];
  }

  return decoded;
}

function parseParameters(value) {
  const parameters = Object.create(null);
  const str = String(value);
  let start = 0;
  let quoted = false;
  let escaped = false;

  function parseParameter(end) {
    const part = trimOWS(str.slice(start, end));
    const equals = part.indexOf('=');

    if (equals < 1) {
      return;
    }

    const name = trimOWS(part.slice(0, equals));

    if (!parameterNameRE.test(name)) {
      return;
    }

    const normalizedName = name.toLowerCase();

    if (
      normalizedName === '__proto__' ||
      normalizedName === 'constructor' ||
      normalizedName === 'prototype'
    ) {
      return;
    }

    const parameterValue = trimOWS(part.slice(equals + 1));
    parameters[normalizedName] = decodeQuotedString(parameterValue);
  }

  for (let i = 0; i < str.length; i++) {
    const code = str.charCodeAt(i);

    if (quoted) {
      if (escaped) {
        escaped = false;
      } else if (code === 0x5c) {
        escaped = true;
      } else if (code === 0x22) {
        quoted = false;
      }
    } else if (code === 0x22) {
      quoted = true;
    } else if (code === 0x2c || code === 0x3b) {
      parseParameter(i);
      start = i + 1;
    }
  }

  parseParameter(str.length);

  return parameters;
}

const isValidHeaderName = (str) => /^[-_a-zA-Z0-9^`|~,!#$%&'*+.]+$/.test(str.trim());

// `__proto__` is a valid field name, and the one name the uppercase mapping at
// the bottom of this file cannot reach: it is inherited from Object.prototype
// instead of being declared on AxiosHeaders.prototype, so `self.__proto__ = v`
// runs the inherited setter. That silently discards the header, and an array
// value replaces the instance prototype, taking every method with it.
// Store it under the same kind of case variant that mapping uses for `set` and
// `constructor`. Header lookup is caseless, so it reads back under either
// spelling, and no own `__proto__` slot is ever created for a later
// `Object.assign` to copy onto a plain object through the same setter.
const PROTO_HEADER_SLOT = '__Proto__';

const headerSlot = (name) => (name === '__proto__' ? PROTO_HEADER_SLOT : name);

function matchHeaderValue(context, value, header, filter, isHeaderNameFilter) {
  if (utils$1.isFunction(filter)) {
    return filter.call(context, value, header);
  }

  if (isHeaderNameFilter) {
    value = header;
  }

  if (!utils$1.isString(value)) return;

  if (utils$1.isString(filter)) {
    return value.indexOf(filter) !== -1;
  }

  if (utils$1.isRegExp(filter)) {
    return filter.test(value);
  }
}

function formatHeader(header) {
  return header
    .trim()
    .toLowerCase()
    .replace(/([a-z\d])(\w*)/g, (w, char, str) => {
      return char.toUpperCase() + str;
    });
}

function buildAccessors(obj, header) {
  const accessorName = utils$1.toCamelCase(' ' + header);

  ['get', 'set', 'has'].forEach((methodName) => {
    Object.defineProperty(obj, methodName + accessorName, {
      // Null-proto descriptor so a polluted Object.prototype.get cannot turn
      // this data descriptor into an accessor descriptor on the way in.
      __proto__: null,
      value: function (arg1, arg2, arg3) {
        return this[methodName].call(this, header, arg1, arg2, arg3);
      },
      configurable: true,
    });
  });
}

class AxiosHeaders {
  constructor(headers) {
    headers && this.set(headers);
  }

  set(header, valueOrRewrite, rewrite) {
    const self = this;

    function setHeader(_value, _header, _rewrite) {
      const lHeader = normalizeHeader(_header);

      if (!lHeader) {
        return;
      }

      const key = utils$1.findKey(self, lHeader);

      if (
        !key ||
        self[key] === undefined ||
        _rewrite === true ||
        (_rewrite === undefined && self[key] !== false)
      ) {
        self[headerSlot(key || _header)] = normalizeValue(_value);
      }
    }

    const setHeaders = (headers, _rewrite) =>
      utils$1.forEach(headers, (_value, _header) => setHeader(_value, _header, _rewrite));

    if (utils$1.isPlainObject(header) || header instanceof this.constructor) {
      setHeaders(header, valueOrRewrite);
    } else if (utils$1.isString(header) && (header = header.trim()) && !isValidHeaderName(header)) {
      setHeaders(parseHeaders(header), valueOrRewrite);
    } else if (utils$1.isObject(header) && utils$1.isSafeIterable(header)) {
      let obj = Object.create(null),
        dest,
        key;
      for (const entry of header) {
        if (!utils$1.isArray(entry)) {
          throw new TypeError('Object iterator must return a key-value pair');
        }

        key = entry[0];

        if (utils$1.hasOwnProp(obj, key)) {
          dest = obj[key];
          obj[key] = utils$1.isArray(dest) ? [...dest, entry[1]] : [dest, entry[1]];
        } else {
          obj[key] = entry[1];
        }
      }

      setHeaders(obj, valueOrRewrite);
    } else {
      header != null && setHeader(valueOrRewrite, header, rewrite);
    }

    return this;
  }

  get(header, parser) {
    header = normalizeHeader(header);

    if (header) {
      const key = utils$1.findKey(this, header);

      if (key) {
        const value = this[key];

        if (!parser) {
          return value;
        }

        if (parser === true) {
          return parseTokens(value);
        }

        if (utils$1.isFunction(parser)) {
          return parser.call(this, value, key);
        }

        if (utils$1.isRegExp(parser)) {
          return parser.exec(value);
        }

        throw new TypeError('parser must be boolean|regexp|function');
      }
    }
  }

  has(header, matcher) {
    header = normalizeHeader(header);

    if (header) {
      const key = utils$1.findKey(this, header);

      return !!(
        key &&
        this[key] !== undefined &&
        (!matcher || matchHeaderValue(this, this[key], key, matcher))
      );
    }

    return false;
  }

  delete(header, matcher) {
    const self = this;
    let deleted = false;

    function deleteHeader(_header) {
      _header = normalizeHeader(_header);

      if (_header) {
        const key = utils$1.findKey(self, _header);

        if (key && (!matcher || matchHeaderValue(self, self[key], key, matcher))) {
          delete self[key];

          deleted = true;
        }
      }
    }

    if (utils$1.isArray(header)) {
      header.forEach(deleteHeader);
    } else {
      deleteHeader(header);
    }

    return deleted;
  }

  clear(matcher) {
    const keys = Object.keys(this);
    let i = keys.length;
    let deleted = false;

    while (i--) {
      const key = keys[i];
      if (!matcher || matchHeaderValue(this, this[key], key, matcher, true)) {
        delete this[key];
        deleted = true;
      }
    }

    return deleted;
  }

  normalize(format) {
    const self = this;
    const headers = Object.create(null);

    utils$1.forEach(this, (value, header) => {
      const key = utils$1.findKey(headers, header);

      if (key) {
        self[key] = normalizeValue(value);
        delete self[header];
        return;
      }

      const normalized = headerSlot(format ? formatHeader(header) : String(header).trim());

      if (normalized !== header) {
        delete self[header];
      }

      self[normalized] = normalizeValue(value);

      headers[normalized] = true;
    });

    return this;
  }

  concat(...targets) {
    return this.constructor.concat(this, ...targets);
  }

  toJSON(asStrings) {
    const obj = Object.create(null);

    utils$1.forEach(this, (value, header) => {
      value != null &&
        value !== false &&
        (obj[header] = asStrings && utils$1.isArray(value) ? value.join(', ') : value);
    });

    return obj;
  }

  [Symbol.iterator]() {
    return Object.entries(this.toJSON())[Symbol.iterator]();
  }

  toString() {
    return Object.entries(this.toJSON())
      .map(([header, value]) => header + ': ' + value)
      .join('\n');
  }

  getSetCookie() {
    const value = this.get('set-cookie');
    return utils$1.isArray(value) ? value : value == null || value === false ? [] : [value];
  }

  get [Symbol.toStringTag]() {
    return 'AxiosHeaders';
  }

  static from(thing) {
    return thing instanceof this ? thing : new this(thing);
  }

  static parseParameters(value) {
    return parseParameters(value);
  }

  static concat(first, ...targets) {
    const computed = new this(first);

    targets.forEach((target) => computed.set(target));

    return computed;
  }

  static accessor(header) {
    const internals =
      (this[$internals$1] =
      this[$internals$1] =
        {
          accessors: {},
        });

    const accessors = internals.accessors;
    const prototype = this.prototype;

    function defineAccessor(_header) {
      const lHeader = normalizeHeader(_header);

      if (!accessors[lHeader]) {
        buildAccessors(prototype, _header);
        accessors[lHeader] = true;
      }
    }

    utils$1.isArray(header) ? header.forEach(defineAccessor) : defineAccessor(header);

    return this;
  }
}

AxiosHeaders.accessor([
  'Content-Type',
  'Content-Length',
  'Accept',
  'Accept-Encoding',
  'User-Agent',
  'Authorization',
]);

// reserved names hotfix
utils$1.reduceDescriptors(AxiosHeaders.prototype, ({ value }, key) => {
  let mapped = key[0].toUpperCase() + key.slice(1); // map `set` => `Set`
  return {
    get: () => value,
    set(headerValue) {
      this[mapped] = headerValue;
    },
  };
});

utils$1.freezeMethods(AxiosHeaders);

const AxiosHeaders$1 = AxiosHeaders;

const REDACTED = '[REDACTED ****]';

function hasOwnOrPrototypeToJSON(source) {
  if (utils$1.hasOwnProp(source, 'toJSON')) {
    return true;
  }

  let prototype = Object.getPrototypeOf(source);

  while (prototype && prototype !== Object.prototype) {
    if (utils$1.hasOwnProp(prototype, 'toJSON')) {
      return true;
    }

    prototype = Object.getPrototypeOf(prototype);
  }

  return false;
}

// Build a plain-object snapshot of `config` and replace the value of any key
// (case-insensitive) listed in `redactKeys` with REDACTED. Walks through arrays
// and AxiosHeaders, and short-circuits on circular references.
function redactConfig(config, redactKeys) {
  const lowerKeys = new Set(redactKeys.map((k) => String(k).toLowerCase()));
  const seen = [];

  const visit = (source) => {
    if (source === null || typeof source !== 'object') return source;
    if (utils$1.isBuffer(source)) return source;
    if (seen.indexOf(source) !== -1) return undefined;

    if (source instanceof AxiosHeaders$1) {
      source = source.toJSON();
    }

    seen.push(source);

    let result;
    if (utils$1.isArray(source)) {
      result = [];
      source.forEach((v, i) => {
        const reducedValue = visit(v);
        if (!utils$1.isUndefined(reducedValue)) {
          result[i] = reducedValue;
        }
      });
    } else {
      if (!utils$1.isPlainObject(source) && hasOwnOrPrototypeToJSON(source)) {
        seen.pop();
        return source;
      }

      result = Object.create(null);
      for (const [key, value] of Object.entries(source)) {
        const reducedValue = lowerKeys.has(key.toLowerCase()) ? REDACTED : visit(value);
        if (!utils$1.isUndefined(reducedValue)) {
          result[key] = reducedValue;
        }
      }
    }

    seen.pop();
    return result;
  };

  return visit(config);
}

function stringifySafely$1(value) {
  try {
    return String(value);
  } catch (err) {
    return '';
  }
}

function aggregateErrorMessage(error) {
  const message = error.errors
    .map((entry) => {
      try {
        return entry && entry.message ? stringifySafely$1(entry.message) : stringifySafely$1(entry);
      } catch (err) {
        return '';
      }
    })
    .filter(Boolean)
    .join('; ');

  return message || error.name || 'AggregateError';
}

// Shared with `Axios.prototype.request`, which splices the reconstructed
// caller frames in ahead of this marker.
const CAUSED_BY_SEPARATOR = '\nCaused by: ';
const $causeStack = Symbol('causeStack');

// Match the section we appended, not marker-like text in an error message or
// a replacement stack supplied by the caller. Do not re-read the cause's stack.
function getCauseStackIndex(error, stack) {
  const causeStack = utils$1.hasOwnProp(error, $causeStack) && error[$causeStack];

  return causeStack && stack.endsWith(causeStack) ? stack.length - causeStack.length : -1;
}

/**
 * Append the stack of a wrapped error to `target.stack`.
 *
 * `cause` already exposes the original error for tooling that walks the standard
 * cause chain, but many error reporters read `stack` and nothing else. Inlining
 * the wrapped stack there means those reporters surface the underlying failure
 * instead of the axios frames that normalized it (see #6670).
 *
 * Every read is defensive: a custom `Error.prepareStackTrace` hook, a runtime
 * without stack support, or a replaced `stack` property can leave the value
 * missing, non-string, or read-only, and normalizing an error must not throw
 * because of that.
 *
 * @param {Error} target The AxiosError being built.
 * @param {Error} source The error being wrapped.
 *
 * @returns {void}
 */
function appendCauseStack(target, source) {
  try {
    const sourceStack = source && source.stack;

    if (typeof sourceStack !== 'string' || !sourceStack) {
      return;
    }

    const targetStack = target.stack;

    if (typeof targetStack !== 'string' || !targetStack) {
      return;
    }

    // Each call to `from()` creates a fresh target. Re-wrapping includes the
    // previous stack verbatim, adding one cause section per wrap.
    const causeStack = CAUSED_BY_SEPARATOR + sourceStack;
    target.stack = targetStack + causeStack;
    Object.defineProperty(target, $causeStack, { __proto__: null, value: causeStack });
  } catch (e) {
    // Ignore failures from custom stack hooks or un-writable stack properties.
  }
}

class AxiosError extends Error {
  static from(error, code, config, request, response, customProps) {
    // `AggregateError` (thrown by Node on dual-stack/Happy-Eyeballs connection
    // failures) has an empty `message`; its detail lives in `errors[]`. Without
    // this, the wrapped error surfaces with a blank message (see #6721).
    let message = error.message;
    if (!message && utils$1.isArray(error.errors) && error.errors.length) {
      message = aggregateErrorMessage(error);
    }

    const axiosError = new AxiosError(message, code || error.code, config, request, response);
    // Match native `Error` `cause` semantics: non-enumerable. The wrapped
    // error often carries circular internals (sockets, requests, agents), so
    // an enumerable `cause` makes structured loggers (pino/winston) and any
    // own-property walk throw "Converting circular structure to JSON".
    // Regression from #6982; see #7205. `__proto__: null` mirrors the
    // `message` descriptor below (prototype-pollution-safe descriptor).
    Object.defineProperty(axiosError, 'cause', {
      __proto__: null,
      value: error,
      writable: true,
      enumerable: false,
      configurable: true,
    });
    axiosError.name = error.name;

    // Inline the wrapped stack for reporters that read only `stack`; the `cause`
    // property above already covers cause-aware tooling.
    appendCauseStack(axiosError, error);

    // Preserve status from the original error if not already set from response
    if (error.status != null && axiosError.status == null) {
      axiosError.status = error.status;
    }

    customProps && Object.assign(axiosError, customProps);
    return axiosError;
  }

  /**
   * Create an Error with the specified message, config, error code, request and response.
   *
   * @param {string} message The error message.
   * @param {string} [code] The error code (for example, 'ECONNABORTED').
   * @param {Object} [config] The config.
   * @param {Object} [request] The request.
   * @param {Object} [response] The response.
   *
   * @returns {Error} The created error.
   */
  constructor(message, code, config, request, response) {
    super(message);

    // Make message enumerable to maintain backward compatibility
    // The native Error constructor sets message as non-enumerable,
    // but axios < v1.13.3 had it as enumerable
    Object.defineProperty(this, 'message', {
      // Null-proto descriptor so a polluted Object.prototype.get cannot turn
      // this data descriptor into an accessor descriptor on the way in.
      __proto__: null,
      value: message,
      enumerable: true,
      writable: true,
      configurable: true,
    });

    this.name = 'AxiosError';
    this.isAxiosError = true;
    code && (this.code = code);
    config && (this.config = config);
    request && (this.request = request);
    if (response) {
      this.response = response;
      this.status = response.status;
    }
  }

  toJSON() {
    // Opt-in redaction: when the request config carries a `redact` array, the
    // value of any matching key (case-insensitive, at any depth) is replaced
    // with REDACTED in the serialized snapshot. Undefined or empty leaves the
    // existing serialization behavior unchanged.
    const config = this.config;
    const redactKeys = config && utils$1.hasOwnProp(config, 'redact') ? config.redact : undefined;
    const serializedConfig =
      utils$1.isArray(redactKeys) && redactKeys.length > 0
        ? redactConfig(config, redactKeys)
        : utils$1.toJSONObject(config);

    return {
      // Standard
      message: this.message,
      name: this.name,
      // Microsoft
      description: this.description,
      number: this.number,
      // Mozilla
      fileName: this.fileName,
      lineNumber: this.lineNumber,
      columnNumber: this.columnNumber,
      stack: this.stack,
      // Axios
      config: serializedConfig,
      code: this.code,
      status: this.status,
    };
  }
}

// This can be changed to static properties as soon as the parser options in .eslint.cjs are updated.
AxiosError.ERR_BAD_OPTION_VALUE = 'ERR_BAD_OPTION_VALUE';
AxiosError.ERR_BAD_OPTION = 'ERR_BAD_OPTION';
AxiosError.ECONNABORTED = 'ECONNABORTED';
AxiosError.ETIMEDOUT = 'ETIMEDOUT';
AxiosError.ECONNREFUSED = 'ECONNREFUSED';
AxiosError.ERR_NETWORK = 'ERR_NETWORK';
AxiosError.ERR_FR_TOO_MANY_REDIRECTS = 'ERR_FR_TOO_MANY_REDIRECTS';
AxiosError.ERR_DEPRECATED = 'ERR_DEPRECATED';
AxiosError.ERR_BAD_RESPONSE = 'ERR_BAD_RESPONSE';
AxiosError.ERR_BAD_REQUEST = 'ERR_BAD_REQUEST';
AxiosError.ERR_CANCELED = 'ERR_CANCELED';
AxiosError.ERR_NOT_SUPPORT = 'ERR_NOT_SUPPORT';
AxiosError.ERR_INVALID_URL = 'ERR_INVALID_URL';
AxiosError.ERR_FORM_DATA_DEPTH_EXCEEDED = 'ERR_FORM_DATA_DEPTH_EXCEEDED';

const AxiosError$1 = AxiosError;

// eslint-disable-next-line strict
const httpAdapter = null;

// Default nesting limit shared with the inverse transform (formDataToJSON) so
// the FormData <-> JSON round-trip stays symmetric.
const DEFAULT_FORM_DATA_MAX_DEPTH = 100;

/**
 * Determines if the given thing is a array or js object.
 *
 * @param {string} thing - The object or array to be visited.
 *
 * @returns {boolean}
 */
function isVisitable(thing) {
  return utils$1.isPlainObject(thing) || utils$1.isArray(thing);
}

/**
 * It removes the brackets from the end of a string
 *
 * @param {string} key - The key of the parameter.
 *
 * @returns {string} the key without the brackets.
 */
function removeBrackets(key) {
  return utils$1.endsWith(key, '[]') ? key.slice(0, -2) : key;
}

/**
 * It takes a path, a key, and a boolean, and returns a string
 *
 * @param {string} path - The path to the current key.
 * @param {string} key - The key of the current object being iterated over.
 * @param {string} dots - If true, the key will be rendered with dots instead of brackets.
 *
 * @returns {string} The path to the current key.
 */
function renderKey(path, key, dots) {
  if (!path) return key;
  return path
    .concat(key)
    .map(function each(token, i) {
      // eslint-disable-next-line no-param-reassign
      token = removeBrackets(token);
      return !dots && i ? '[' + token + ']' : token;
    })
    .join(dots ? '.' : '');
}

/**
 * If the array is an array and none of its elements are visitable, then it's a flat array.
 *
 * @param {Array<any>} arr - The array to check
 *
 * @returns {boolean}
 */
function isFlatArray(arr) {
  return utils$1.isArray(arr) && !arr.some(isVisitable);
}

const predicates = utils$1.toFlatObject(utils$1, {}, null, function filter(prop) {
  return /^is[A-Z]/.test(prop);
});

/**
 * Convert a data object to FormData
 *
 * @param {Object} obj
 * @param {?Object} [formData]
 * @param {?Object} [options]
 * @param {Function} [options.visitor]
 * @param {Boolean} [options.metaTokens = true]
 * @param {Boolean} [options.dots = false]
 * @param {?Boolean} [options.indexes = false]
 *
 * @returns {Object}
 **/

/**
 * It converts an object into a FormData object
 *
 * @param {Object<any, any>} obj - The object to convert to form data.
 * @param {string} formData - The FormData object to append to.
 * @param {Object<string, any>} options
 *
 * @returns
 */
function toFormData(obj, formData, options) {
  if (!utils$1.isObject(obj)) {
    throw new TypeError('target must be an object');
  }

  // eslint-disable-next-line no-param-reassign
  formData = formData || new (FormData)();

  const option = (name, fallback) => {
    const value = utils$1.getSafeProp(options, name);
    return utils$1.isUndefined(value) ? fallback : value;
  };

  const metaTokens = option('metaTokens', true);
  // eslint-disable-next-line no-use-before-define
  const visitor = option('visitor') || defaultVisitor;
  const dots = option('dots', false);
  const indexes = option('indexes', false);
  const _Blob = option('Blob') || (typeof Blob !== 'undefined' && Blob);
  const maxDepth = option('maxDepth', DEFAULT_FORM_DATA_MAX_DEPTH);
  const useBlob = _Blob && utils$1.isSpecCompliantForm(formData);
  const stack = [];

  if (!utils$1.isFunction(visitor)) {
    throw new TypeError('visitor must be a function');
  }

  function convertValue(value) {
    if (value === null) return '';

    if (utils$1.isDate(value)) {
      return value.toISOString();
    }

    if (utils$1.isBoolean(value)) {
      return value.toString();
    }

    if (!useBlob && utils$1.isBlob(value)) {
      throw new AxiosError$1('Blob is not supported. Use a Buffer instead.');
    }

    if (utils$1.isArrayBuffer(value) || utils$1.isTypedArray(value)) {
      if (useBlob && typeof _Blob === 'function') {
        return new _Blob([value]);
      }
      throw new AxiosError$1(
        'Blob is not supported. Use a Buffer instead.',
        AxiosError$1.ERR_NOT_SUPPORT
      );
    }

    return value;
  }

  function throwIfMaxDepthExceeded(depth) {
    if (depth > maxDepth) {
      throw new AxiosError$1(
        'Object is too deeply nested (' + depth + ' levels). Max depth: ' + maxDepth,
        AxiosError$1.ERR_FORM_DATA_DEPTH_EXCEEDED
      );
    }
  }

  function stringifyWithDepthLimit(value, depth) {
    if (maxDepth === Infinity) {
      return JSON.stringify(value);
    }

    const ancestors = [];

    return JSON.stringify(value, function limitDepth(_key, currentValue) {
      if (!utils$1.isObject(currentValue)) {
        return currentValue;
      }

      while (ancestors.length && ancestors[ancestors.length - 1] !== this) {
        ancestors.pop();
      }

      ancestors.push(currentValue);
      throwIfMaxDepthExceeded(depth + ancestors.length - 1);

      return currentValue;
    });
  }

  /**
   * Default visitor.
   *
   * @param {*} value
   * @param {String|Number} key
   * @param {Array<String|Number>} path
   * @this {FormData}
   *
   * @returns {boolean} return true to visit the each prop of the value recursively
   */
  function defaultVisitor(value, key, path) {
    let arr = value;

    if (utils$1.isReactNative(formData) && utils$1.isReactNativeBlob(value)) {
      formData.append(renderKey(path, key, dots), convertValue(value));
      return false;
    }

    if (value && !path && typeof value === 'object') {
      if (utils$1.endsWith(key, '{}')) {
        // eslint-disable-next-line no-param-reassign
        key = metaTokens ? key : key.slice(0, -2);
        // eslint-disable-next-line no-param-reassign
        value = stringifyWithDepthLimit(value, 1);
      } else if (
        (utils$1.isArray(value) && isFlatArray(value)) ||
        ((utils$1.isFileList(value) || utils$1.endsWith(key, '[]')) && (arr = utils$1.toArray(value)))
      ) {
        // eslint-disable-next-line no-param-reassign
        key = removeBrackets(key);

        arr.forEach(function each(el, index) {
          !(utils$1.isUndefined(el) || el === null) &&
            formData.append(
              // eslint-disable-next-line no-nested-ternary
              indexes === true
                ? renderKey([key], index, dots)
                : indexes === null
                  ? key
                  : key + '[]',
              convertValue(el)
            );
        });
        return false;
      }
    }

    if (isVisitable(value)) {
      return true;
    }

    formData.append(renderKey(path, key, dots), convertValue(value));

    return false;
  }

  const exposedHelpers = Object.assign(predicates, {
    defaultVisitor,
    convertValue,
    isVisitable,
  });

  function build(value, path, depth = 0) {
    if (utils$1.isUndefined(value)) return;

    throwIfMaxDepthExceeded(depth);

    if (stack.indexOf(value) !== -1) {
      throw new Error('Circular reference detected in ' + path.join('.'));
    }

    stack.push(value);

    utils$1.forEach(value, function each(el, key) {
      const result =
        !(utils$1.isUndefined(el) || el === null) &&
        visitor.call(formData, el, utils$1.isString(key) ? key.trim() : key, path, exposedHelpers);

      if (result === true) {
        build(el, path ? path.concat(key) : [key], depth + 1);
      }
    });

    stack.pop();
  }

  if (!utils$1.isObject(obj)) {
    throw new TypeError('data must be an object');
  }

  build(obj);

  return formData;
}

/**
 * It encodes a string by replacing all characters that are not in the unreserved set with
 * their percent-encoded equivalents
 *
 * @param {string} str - The string to encode.
 *
 * @returns {string} The encoded string.
 */
function encode$1(str) {
  const charMap = {
    '!': '%21',
    "'": '%27',
    '(': '%28',
    ')': '%29',
    '~': '%7E',
    '%20': '+',
  };
  return encodeURIComponent(str).replace(/[!'()~]|%20/g, function replacer(match) {
    return charMap[match];
  });
}

/**
 * It takes a params object and converts it to a FormData object
 *
 * @param {Object<string, any>} params - The parameters to be converted to a FormData object.
 * @param {Object<string, any>} options - The options object passed to the Axios constructor.
 *
 * @returns {void}
 */
function AxiosURLSearchParams(params, options) {
  this._pairs = [];

  params && toFormData(params, this, options);
}

const prototype = AxiosURLSearchParams.prototype;

prototype.append = function append(name, value) {
  this._pairs.push([name, value]);
};

prototype.toString = function toString(encoder) {
  const _encode = encoder
    ? (value) => encoder.call(this, value, encode$1)
    : encode$1;

  return this._pairs
    .map(function each(pair) {
      return _encode(pair[0]) + '=' + _encode(pair[1]);
    }, '')
    .join('&');
};

/**
 * It replaces URL-encoded forms of `:`, `$`, `,`, and spaces with
 * their plain counterparts (`:`, `$`, `,`, `+`).
 *
 * @param {string} val The value to be encoded.
 *
 * @returns {string} The encoded value.
 */
function encode(val) {
  return encodeURIComponent(val)
    .replace(/%3A/gi, ':')
    .replace(/%24/g, '$')
    .replace(/%2C/gi, ',')
    .replace(/%20/g, '+');
}

/**
 * Build a URL by appending params to the end
 *
 * @param {string} url The base of the url (e.g., http://www.google.com)
 * @param {object} [params] The params to be appended
 * @param {?(object|Function)} options
 *
 * @returns {string} The formatted url
 */
function buildURL(url, params, options) {
  if (!params) {
    return url;
  }
  url = url || '';

  const _options = utils$1.isFunction(options)
    ? {
        serialize: options,
      }
    : options;

  // Read serializer options pollution-safely: own properties and methods on a
  // class/template prototype are honored, but values injected onto a polluted
  // Object.prototype are ignored.
  const _encode = utils$1.getSafeProp(_options, 'encode') || encode;
  const serializeFn = utils$1.getSafeProp(_options, 'serialize');

  let serializedParams;

  if (serializeFn) {
    serializedParams = serializeFn(params, _options);
  } else {
    serializedParams = utils$1.isURLSearchParams(params)
      ? params.toString()
      : new AxiosURLSearchParams(params, _options).toString(_encode);
  }

  if (serializedParams) {
    const hashmarkIndex = url.indexOf('#');

    if (hashmarkIndex !== -1) {
      url = url.slice(0, hashmarkIndex);
    }
    url += (url.indexOf('?') === -1 ? '?' : '&') + serializedParams;
  }

  return url;
}

const $internals = Symbol('internals');

// `handlers` is public and may be replaced with a nullish value by user code;
// `clear()` has always tolerated that. Treat it as an empty stack rather than
// dereferencing it.
function countHandlers(handlers) {
  return handlers ? handlers.length : 0;
}

function trimHandlers(handlers) {
  if (!handlers) {
    return;
  }

  while (handlers.length && handlers[handlers.length - 1] === null) {
    handlers.pop();
  }
}

// Preserve the array-key coercion used before IDs were stored in a Map, without
// treating null, empty strings, or noncanonical numeric strings as ID zero.
function normalizeHandlerId(id) {
  if (typeof id === 'string' && id !== '' && String(Number(id)) === id) {
    return Number(id);
  }

  return id;
}

function syncHandlerEntries(manager, internals) {
  const handlers = manager.handlers;
  const length = countHandlers(handlers);

  if (handlers !== internals.handlersRef) {
    internals.handlersRef = handlers;
    internals.handlerEntries.clear();
  } else if (length !== internals.handlersLength) {
    if (!length) {
      internals.handlerEntries.clear();
    } else {
      internals.handlerEntries.forEach(function removeStaleEntry(entry, id) {
        if (handlers[entry.index] !== entry.handler) {
          internals.handlerEntries.delete(id);
        }
      });
    }
  }

  internals.handlersLength = length;
}

class InterceptorManager {
  constructor() {
    this.handlers = [];
    this[$internals] = {
      handlersRef: this.handlers,
      handlersLength: this.handlers.length,
      handlerEntries: new Map(),
      iterationDepth: 0,
      nextId: 0,
    };
  }

  /**
   * Add a new interceptor to the stack
   *
   * @param {Function} fulfilled The function to handle `then` for a `Promise`
   * @param {Function} rejected The function to handle `reject` for a `Promise`
   * @param {Object} options The options for the interceptor, synchronous and runWhen
   *
   * @return {Number} An ID used to remove interceptor later
   */
  use(fulfilled, rejected, options) {
    const handler = {
      fulfilled,
      rejected,
      synchronous: options ? options.synchronous : false,
      runWhen: options ? options.runWhen : null,
    };
    const internals = this[$internals];

    if (this.handlers == null) {
      this.handlers = [];
    }

    syncHandlerEntries(this, internals);

    const id = internals.nextId++;

    this.handlers.push(handler);
    internals.handlerEntries.set(id, {
      handler,
      index: this.handlers.length - 1,
    });
    internals.handlersLength = this.handlers.length;

    return id;
  }

  /**
   * Remove an interceptor from the stack
   *
   * @param {Number} id The ID that was returned by `use`
   *
   * @returns {void}
   */
  eject(id) {
    const internals = this[$internals];

    syncHandlerEntries(this, internals);

    const handlerId = normalizeHandlerId(id);
    const entry = internals.handlerEntries.get(handlerId);

    if (entry) {
      internals.handlerEntries.delete(handlerId);

      // Ignore IDs invalidated by clear or direct replacement of handlers.
      if (this.handlers[entry.index] !== entry.handler) {
        return;
      }

      this.handlers[entry.index] = null;

      // Do not reuse an index while forEach is walking its length snapshot.
      if (!internals.iterationDepth) {
        trimHandlers(this.handlers);
        internals.handlersLength = this.handlers.length;
      }
    }
  }

  /**
   * Clear all interceptors from the stack
   *
   * @returns {void}
   */
  clear() {
    if (this.handlers) {
      this.handlers = [];
      syncHandlerEntries(this, this[$internals]);
    }
  }

  /**
   * Iterate over all the registered interceptors
   *
   * This method is particularly useful for skipping over any
   * interceptors that may have become `null` calling `eject`.
   *
   * @param {Function} fn The function to call for each interceptor
   *
   * @returns {void}
   */
  forEach(fn) {
    const internals = this[$internals];

    syncHandlerEntries(this, internals);

    internals.iterationDepth++;

    try {
      utils$1.forEach(this.handlers, function forEachHandler(h) {
        if (h !== null) {
          fn(h);
        }
      });
    } finally {
      if (!--internals.iterationDepth) {
        syncHandlerEntries(this, internals);
        trimHandlers(this.handlers);
        internals.handlersLength = countHandlers(this.handlers);
      }
    }
  }
}

const InterceptorManager$1 = InterceptorManager;

const transitionalDefaults = {
  silentJSONParsing: true,
  forcedJSONParsing: true,
  clarifyTimeoutError: false,
  legacyInterceptorReqResOrdering: true,
  advertiseZstdAcceptEncoding: false,
  validateStatusUndefinedResolves: true,
  encodeBasicAuthUsername: false,
};

const URLSearchParams$1 = typeof URLSearchParams !== 'undefined' ? URLSearchParams : AxiosURLSearchParams;

const FormData$1 = typeof FormData !== 'undefined' ? FormData : null;

const Blob$1 = typeof Blob !== 'undefined' ? Blob : null;

const platform$1 = {
  isBrowser: true,
  classes: {
    URLSearchParams: URLSearchParams$1,
    FormData: FormData$1,
    Blob: Blob$1,
  },
  protocols: ['http', 'https', 'file', 'blob', 'url', 'data'],
};

const hasBrowserEnv = typeof window !== 'undefined' && typeof document !== 'undefined';

const _navigator = (typeof navigator === 'object' && navigator) || undefined;

/**
 * Determine if we're running in a standard browser environment
 *
 * This allows axios to run in a web worker, and react-native.
 * Both environments support XMLHttpRequest, but not fully standard globals.
 *
 * web workers:
 *  typeof window -> undefined
 *  typeof document -> undefined
 *
 * react-native:
 *  navigator.product -> 'ReactNative'
 * nativescript
 *  navigator.product -> 'NativeScript' or 'NS'
 *
 * @returns {boolean}
 */
const hasStandardBrowserEnv =
  hasBrowserEnv &&
  (!_navigator || ['ReactNative', 'NativeScript', 'NS'].indexOf(_navigator.product) < 0);

/**
 * Determine if we're running in a standard browser webWorker environment
 *
 * Although the `isStandardBrowserEnv` method indicates that
 * `allows axios to run in a web worker`, the WebWorker will still be
 * filtered out due to its judgment standard
 * `typeof window !== 'undefined' && typeof document !== 'undefined'`.
 * This leads to a problem when axios post `FormData` in webWorker
 */
const hasStandardBrowserWebWorkerEnv = (() => {
  return (
    typeof WorkerGlobalScope !== 'undefined' &&
    // eslint-disable-next-line no-undef
    self instanceof WorkerGlobalScope &&
    typeof self.importScripts === 'function'
  );
})();

const origin = (hasBrowserEnv && window.location.href) || 'http://localhost';

const utils = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.defineProperty({
  __proto__: null,
  hasBrowserEnv,
  hasStandardBrowserEnv,
  hasStandardBrowserWebWorkerEnv,
  navigator: _navigator,
  origin
}, Symbol.toStringTag, { value: 'Module' }));

const platform = {
  ...utils,
  ...platform$1,
};

function toURLEncodedForm(data, options) {
  return toFormData(data, new platform.classes.URLSearchParams(), {
    visitor: function (value, key, path, helpers) {
      if (platform.isNode && utils$1.isBuffer(value)) {
        this.append(key, value.toString('base64'));
        return false;
      }

      return helpers.defaultVisitor.apply(this, arguments);
    },
    ...options,
  });
}

const MAX_DEPTH = DEFAULT_FORM_DATA_MAX_DEPTH;

function throwIfDepthExceeded(index) {
  if (index > MAX_DEPTH) {
    throw new AxiosError$1(
      'FormData field is too deeply nested (' + index + ' levels). Max depth: ' + MAX_DEPTH,
      AxiosError$1.ERR_FORM_DATA_DEPTH_EXCEEDED
    );
  }
}

/**
 * It takes a string like `foo[x][y][z]` and returns an array like `['foo', 'x', 'y', 'z']
 *
 * @param {string} name - The name of the property to get.
 *
 * @returns An array of strings.
 */
function parsePropPath(name) {
  // foo[x][y][z] -> ['foo', 'x', 'y', 'z']
  // foo.x.y.z    -> ['foo', 'x', 'y', 'z']
  // A path is split on `.` and on `[...]` groups. A segment — whether written
  // in dot notation or captured inside brackets — may contain any character
  // except `.`, `[` and `]`, so a key like `user-name` or `user name` is kept
  // literal instead of being split (#5402). `.`, `[` and `]` keep their existing
  // meaning, e.g. `foo[bar.baz]` -> ['foo', 'bar', 'baz'] and `[]` is an array push.
  // Excluding `[` from the bracket group also makes the match fail fast at the
  // next `[`, so a malformed name cannot rescan to the end of the string from
  // every unmatched `[` — parsing stays linear in the length of the name.
  const path = [];
  const pattern = /[^.[\]]+|\[([^.[\]]*)]/g;
  let match;

  while ((match = pattern.exec(name)) !== null) {
    throwIfDepthExceeded(path.length);
    path.push(match[0] === '[]' ? '' : match[1] || match[0]);
  }

  return path;
}

/**
 * Convert an array to an object.
 *
 * @param {Array<any>} arr - The array to convert to an object.
 *
 * @returns An object with the same keys and values as the array.
 */
function arrayToObject(arr) {
  const obj = {};
  const keys = Object.keys(arr);
  let i;
  const len = keys.length;
  let key;
  for (i = 0; i < len; i++) {
    key = keys[i];
    obj[key] = arr[key];
  }
  return obj;
}

function normalizeArray(value) {
  if (!utils$1.isArray(value)) return value;

  const keys = Object.keys(value);
  return keys.length !== value.length || keys.some((key, index) => key !== String(index))
    ? arrayToObject(value)
    : value;
}

function normalizeArrays(obj) {
  const pending = [obj];
  while (pending.length) {
    const target = pending.pop();
    Object.keys(target).forEach((key) => {
      const value = (target[key] = normalizeArray(target[key]));
      if (utils$1.isArray(value) || utils$1.isPlainObject(value)) {
        pending.push(value);
      }
    });
  }
  return obj;
}

/**
 * It takes a FormData object and returns a JavaScript object
 *
 * @param {string} formData The FormData object to convert to JSON.
 *
 * @returns {Object<string, any> | null} The converted object.
 */
function formDataToJSON(formData) {
  function buildPath(path, value, target, index) {
    throwIfDepthExceeded(index);

    let name = path[index++];

    if (name === '__proto__') return true;

    const isNumericKey = Number.isFinite(+name);
    const isLast = index >= path.length;
    name = !name && utils$1.isArray(target) ? target.length : name;

    if (isLast) {
      if (utils$1.hasOwnProp(target, name)) {
        target[name] = normalizeArray(target[name]);
        target[name] = utils$1.isArray(target[name])
          ? target[name].concat(value)
          : [target[name], value];
      } else {
        target[name] = value;
      }

      return !isNumericKey;
    }

    if (!utils$1.hasOwnProp(target, name) || !utils$1.isObject(target[name])) {
      target[name] = [];
    }

    const result = buildPath(path, value, target[name], index);

    if (result && utils$1.isArray(target[name])) {
      target[name] = arrayToObject(target[name]);
    }

    return !isNumericKey;
  }

  if (utils$1.isFormData(formData) && utils$1.isFunction(formData.entries)) {
    const obj = {};

    utils$1.forEachEntry(formData, (name, value) => {
      buildPath(parsePropPath(name), value, obj, 0);
    });

    return normalizeArrays(obj);
  }

  return null;
}

const methodList = Object.freeze([
  'get',
  'delete',
  'head',
  'options',
  'post',
  'put',
  'patch',
  'purge',
  'link',
  'unlink',
  'query',
]);

const methodList$1 = methodList;

const own = (obj, key) => (obj != null && utils$1.hasOwnProp(obj, key) ? obj[key] : undefined);

/**
 * It takes a string, tries to parse it, and if it fails, it returns the stringified version
 * of the input
 *
 * @param {any} rawValue - The value to be stringified.
 * @param {Function} parser - A function that parses a string into a JavaScript object.
 * @param {Function} encoder - A function that takes a value and returns a string.
 *
 * @returns {string} A stringified version of the rawValue.
 */
function stringifySafely(rawValue, parser, encoder) {
  if (utils$1.isString(rawValue)) {
    try {
      (parser || JSON.parse)(rawValue);
      return utils$1.trim(rawValue);
    } catch (e) {
      if (e.name !== 'SyntaxError') {
        throw e;
      }
    }
  }

  return (encoder || JSON.stringify)(rawValue);
}

const defaults = {
  transitional: transitionalDefaults,

  adapter: ['xhr', 'http', 'fetch'],

  transformRequest: [
    function transformRequest(data, headers) {
      const contentType = headers.getContentType() || '';
      const hasJSONContentType = contentType.indexOf('application/json') > -1;
      const isObjectPayload = utils$1.isObject(data);

      if (isObjectPayload && utils$1.isHTMLForm(data)) {
        data = new FormData(data);
      }

      const isFormData = utils$1.isFormData(data);

      if (isFormData) {
        return hasJSONContentType ? JSON.stringify(formDataToJSON(data)) : data;
      }

      if (
        utils$1.isArrayBuffer(data) ||
        utils$1.isBuffer(data) ||
        utils$1.isStream(data) ||
        utils$1.isFile(data) ||
        utils$1.isBlob(data) ||
        utils$1.isReadableStream(data)
      ) {
        return data;
      }
      if (utils$1.isArrayBufferView(data)) {
        return data.buffer;
      }
      if (utils$1.isURLSearchParams(data)) {
        headers.setContentType('application/x-www-form-urlencoded;charset=utf-8', false);
        return data.toString();
      }

      let isFileList;

      if (isObjectPayload) {
        const formSerializer = own(this, 'formSerializer');
        if (contentType.indexOf('application/x-www-form-urlencoded') > -1) {
          return toURLEncodedForm(data, formSerializer).toString();
        }

        if (
          (isFileList = utils$1.isFileList(data)) ||
          contentType.indexOf('multipart/form-data') > -1
        ) {
          const env = own(this, 'env');
          const _FormData = env && env.FormData;

          return toFormData(
            isFileList ? { 'files[]': data } : data,
            _FormData && new _FormData(),
            formSerializer
          );
        }
      }

      if (isObjectPayload || hasJSONContentType) {
        headers.setContentType('application/json', false);
        return stringifySafely(data);
      }

      return data;
    },
  ],

  transformResponse: [
    function transformResponse(data) {
      const transitional = own(this, 'transitional') || defaults.transitional;
      const forcedJSONParsing = transitional && transitional.forcedJSONParsing;
      const responseType = own(this, 'responseType');
      const JSONRequested = responseType === 'json';

      if (utils$1.isResponse(data) || utils$1.isReadableStream(data)) {
        return data;
      }

      if (
        data &&
        utils$1.isString(data) &&
        ((forcedJSONParsing && !responseType) || JSONRequested)
      ) {
        const silentJSONParsing = transitional && transitional.silentJSONParsing;
        const strictJSONParsing = !silentJSONParsing && JSONRequested;

        try {
          return JSON.parse(data, own(this, 'parseReviver'));
        } catch (e) {
          if (strictJSONParsing) {
            if (e.name === 'SyntaxError') {
              throw AxiosError$1.from(e, AxiosError$1.ERR_BAD_RESPONSE, this, null, own(this, 'response'));
            }
            throw e;
          }
        }
      }

      return data;
    },
  ],

  /**
   * A timeout in milliseconds to abort a request. If set to 0 (default) a
   * timeout is not created.
   */
  timeout: 0,

  xsrfCookieName: 'XSRF-TOKEN',
  xsrfHeaderName: 'X-XSRF-TOKEN',

  maxContentLength: -1,
  maxBodyLength: -1,

  env: {
    FormData: platform.classes.FormData,
    Blob: platform.classes.Blob,
  },

  validateStatus: function validateStatus(status) {
    return status >= 200 && status < 300;
  },

  headers: {
    common: {
      Accept: 'application/json, text/plain, */*',
      'Content-Type': undefined,
    },
  },
};

utils$1.forEach(methodList$1, (method) => {
  defaults.headers[method] = {};
});

const defaults$1 = defaults;

/**
 * Transform the data for a request or a response
 *
 * @param {Array|Function} fns A single function or Array of functions
 * @param {?Object} response The response object
 *
 * @returns {*} The resulting transformed data
 */
function transformData(fns, response) {
  const config = this || defaults$1;
  const context = response || config;
  const headers = AxiosHeaders$1.from(context.headers);
  let data = context.data;

  utils$1.forEach(fns, function transform(fn) {
    data = fn.call(config, data, headers.normalize(), response ? response.status : undefined);
  });

  headers.normalize();

  return data;
}

function isCancel(value) {
  return !!(value && value.__CANCEL__);
}

class CanceledError extends AxiosError$1 {
  /**
   * A `CanceledError` is an object that is thrown when an operation is canceled.
   *
   * @param {string=} message The message.
   * @param {Object=} config The config.
   * @param {Object=} request The request.
   *
   * @returns {CanceledError} The created error.
   */
  constructor(message, config, request) {
    super(message == null ? 'canceled' : message, AxiosError$1.ERR_CANCELED, config, request);
    this.name = 'CanceledError';
    this.__CANCEL__ = true;
  }
}

const CanceledError$1 = CanceledError;

/**
 * Resolve or reject a Promise based on response status.
 *
 * @param {Function} resolve A function that resolves the promise.
 * @param {Function} reject A function that rejects the promise.
 * @param {object} response The response.
 *
 * @returns {object} The response.
 */
function settle(resolve, reject, response) {
  const validateStatus = response.config.validateStatus;
  if (!response.status || !validateStatus || validateStatus(response.status)) {
    resolve(response);
  } else {
    reject(new AxiosError$1(
      'Request failed with status code ' + response.status,
      response.status >= 400 && response.status < 500 ? AxiosError$1.ERR_BAD_REQUEST : AxiosError$1.ERR_BAD_RESPONSE,
      response.config,
      response.request,
      response
    ));
  }
}

const urlParserControlCharacters = /[\t\n\r]/g;

/**
 * Match WHATWG URL preprocessing before checking a URL's protocol.
 *
 * @param {string} url
 *
 * @returns {string}
 */
function normalizeURLForProtocolCheck(url) {
  if (typeof url !== 'string') {
    return url;
  }

  let start = 0;

  while (start < url.length && url.charCodeAt(start) <= 0x20) {
    start++;
  }

  return url.slice(start).replace(urlParserControlCharacters, '');
}

function parseProtocol(url) {
  const match = /^([-+\w]{1,25}):(?:\/\/)?/.exec(url);
  return (match && match[1].toLowerCase()) || '';
}

const decodeCookieValue = (value) => {
  try {
    return decodeURIComponent(value);
  } catch (e) {
    return value;
  }
};

const cookies = platform.hasStandardBrowserEnv
  ? // Standard browser envs support document.cookie
    {
      write(name, value, expires, path, domain, secure, sameSite) {
        if (typeof document === 'undefined') return;

        const cookie = [`${name}=${encodeURIComponent(value)}`];

        if (utils$1.isNumber(expires)) {
          cookie.push(`expires=${new Date(expires).toUTCString()}`);
        }
        if (utils$1.isString(path)) {
          cookie.push(`path=${path}`);
        }
        if (utils$1.isString(domain)) {
          cookie.push(`domain=${domain}`);
        }
        if (secure === true) {
          cookie.push('secure');
        }
        if (utils$1.isString(sameSite)) {
          cookie.push(`SameSite=${sameSite}`);
        }

        document.cookie = cookie.join('; ');
      },

      read(name) {
        if (typeof document === 'undefined') return null;
        const cookieString = document.cookie;
        if (!cookieString) return null;
        // Match name=value by splitting on the semicolon separator instead of building a
        // RegExp from `name` — interpolating an unescaped string into a RegExp would let
        // metacharacters (e.g. `.+?` in an attacker-influenced cookie name) cause ReDoS or
        // match the wrong cookie. Browsers may serialize cookie pairs as either ";" or
        // "; ", so ignore optional whitespace before each cookie name.
        const cookies = cookieString.split(';');
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].replace(/^\s+/, '');
          const eq = cookie.indexOf('=');
          if (eq !== -1 && cookie.slice(0, eq) === name) {
            return decodeCookieValue(cookie.slice(eq + 1));
          }
        }
        return null;
      },

      async readAsync(name) {
        try {
          const store = typeof window !== 'undefined' && window.cookieStore;
          if (store && utils$1.isFunction(store.get)) {
            const cookie = await store.get(name);
            // Both APIs expose stored bytes; preserve Axios's existing URI decoding.
            return cookie ? decodeCookieValue(cookie.value) : null;
          }
        } catch (e) {
          // Restricted or unavailable storage retains the synchronous fallback.
        }

        return this.read(name);
      },

      remove(name) {
        this.write(name, '', Date.now() - 86400000, '/');
      },
    }
  : // Non-standard browser env (web workers, react-native) lack needed support.
    {
      write() {},
      read() {
        return null;
      },
      async readAsync() {
        return null;
      },
      remove() {},
    };

/**
 * Calculate data maxRate
 * @param {Number} [samplesCount= 10]
 * @param {Number} [min= 1000]
 * @returns {Function}
 */
function speedometer(samplesCount, min) {
  samplesCount = samplesCount || 10;
  const bytes = new Array(samplesCount);
  const timestamps = new Array(samplesCount);
  let head = 0;
  let tail = 0;
  let firstSampleTS;

  min = min !== undefined ? min : 1000;

  return function push(chunkLength) {
    const now = Date.now();

    const startedAt = timestamps[tail];

    if (!firstSampleTS) {
      firstSampleTS = now;
    }

    bytes[head] = chunkLength;
    timestamps[head] = now;

    let i = tail;
    let bytesCount = 0;

    while (i !== head) {
      bytesCount += bytes[i++];
      i = i % samplesCount;
    }

    head = (head + 1) % samplesCount;

    if (head === tail) {
      tail = (tail + 1) % samplesCount;
    }

    if (now - firstSampleTS < min) {
      return;
    }

    const passed = startedAt && now - startedAt;

    return passed ? Math.round((bytesCount * 1000) / passed) : undefined;
  };
}

/**
 * Throttle decorator
 * @param {Function} fn
 * @param {Number} freq
 * @return {Array<Function>}
 */
function throttle(fn, freq) {
  let timestamp = 0;
  let threshold = 1000 / freq;
  let lastArgs;
  let timer;

  const invoke = (args, now = Date.now()) => {
    timestamp = now;
    lastArgs = null;
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
    fn(...args);
  };

  const throttled = (...args) => {
    const now = Date.now();
    const passed = now - timestamp;
    if (passed >= threshold) {
      invoke(args, now);
    } else {
      lastArgs = args;
      if (!timer) {
        timer = setTimeout(() => {
          timer = null;
          invoke(lastArgs);
        }, threshold - passed);
      }
    }
  };

  const flush = () => lastArgs && invoke(lastArgs);
  const flushWith = (...args) => invoke(args);

  return [throttled, flush, flushWith];
}

const progressEventReducer = (listener, isDownloadStream, freq = 3) => {
  let bytesNotified = 0;
  const _speedometer = speedometer(50, 250);

  return throttle((e) => {
    if (!e || !utils$1.isNumber(e.loaded)) {
      return;
    }
    const rawLoaded = e.loaded;
    const total = e.lengthComputable ? e.total : undefined;
    const loaded = Math.max(0, total != null ? Math.min(rawLoaded, total) : rawLoaded);
    const progressBytes = Math.max(0, loaded - bytesNotified);
    const rate = _speedometer(progressBytes);

    bytesNotified = Math.max(bytesNotified, loaded);

    const data = {
      loaded,
      total,
      progress: total ? loaded / total : undefined,
      bytes: progressBytes,
      rate: rate ? rate : undefined,
      estimated: rate && total ? (total - loaded) / rate : undefined,
      event: e,
      lengthComputable: total != null,
      [isDownloadStream ? 'download' : 'upload']: true,
    };

    listener(data);
  }, freq);
};

const progressEventDecorator = (total, throttled) => {
  const lengthComputable = total != null;

  return [
    (loaded) =>
      throttled[0]({
        lengthComputable,
        total,
        loaded,
      }),
    throttled[1],
  ];
};

const asyncDecorator =
  (fn, scheduler = utils$1.asap) =>
  (...args) =>
    scheduler(() => fn(...args));

const isURLSameOrigin = platform.hasStandardBrowserEnv
  ? ((origin) => (url) => {
      url = new URL(url, document.baseURI || platform.origin);

      return (
        origin.protocol === url.protocol && origin.host === url.host && origin.port === url.port
      );
    })(new URL(platform.origin))
  : () => true;

/**
 * Determines whether the specified URL is absolute
 *
 * @param {string} url The URL to test
 *
 * @returns {boolean} True if the specified URL is absolute, otherwise false
 */
function isAbsoluteURL(url) {
  // A URL is considered absolute if it begins with "<scheme>://" or "//" (protocol-relative URL).
  // RFC 3986 defines scheme name as a sequence of characters beginning with a letter and followed
  // by any combination of letters, digits, plus, period, or hyphen.
  if (typeof url !== 'string') {
    return false;
  }

  return /^([a-z][a-z\d+\-.]*:)?\/\//i.test(url);
}

/**
 * Creates a new URL by combining the specified URLs
 *
 * @param {string} baseURL The base URL
 * @param {string} relativeURL The relative URL
 *
 * @returns {string} The combined URL
 */
function combineURLs(baseURL, relativeURL) {
  if (!relativeURL) {
    return baseURL;
  }

  let end = baseURL.length;

  while (end > 0 && baseURL.charCodeAt(end - 1) === 47) {
    end--;
  }

  return baseURL.slice(0, end) + '/' + relativeURL.replace(/^\/+/, '');
}

const malformedHttpProtocol = /^https?:(?!\/\/)/i;

// Redact the parts of a URL that can carry secrets before it is embedded in an
// error message. AxiosError.toJSON() serializes `message` verbatim and errors
// are commonly logged, while the opt-in `config.redact` model only cleans
// config keys — it cannot reach the message. Redact only the genuinely
// sensitive substrings — userinfo (credentials), query parameter values and
// fragment contents — with the same REDACTED marker the config redaction uses,
// while keeping the scheme, host, path and parameter names so the offending
// request stays accurately identifiable.
function redactFragment(fragment) {
  if (!fragment) {
    return fragment;
  }

  return fragment.replace(/(^|&)([^=&]*=)?[^&]+/g, (match, separator, parameterName = '') => {
    return `${separator}${parameterName}${REDACTED}`;
  });
}

function redactSensitiveURLParts(url) {
  const redactedURL = url.replace(/^(https?:\/{0,2})[^/?#]*@/i, `$1${REDACTED}@`);
  const fragmentIndex = redactedURL.indexOf('#');
  const urlWithoutFragment =
    fragmentIndex === -1 ? redactedURL : redactedURL.slice(0, fragmentIndex);
  const redactedURLWithoutFragment = urlWithoutFragment.replace(
    /([?&][^=&#]*=)[^&#]*/g,
    `$1${REDACTED}`
  );

  if (fragmentIndex === -1) {
    return redactedURLWithoutFragment;
  }

  return `${redactedURLWithoutFragment}#${redactFragment(redactedURL.slice(fragmentIndex + 1))}`;
}

function assertValidHttpProtocolURL(url, config) {
  if (typeof url === 'string') {
    const normalizedURL = normalizeURLForProtocolCheck(url);
    if (malformedHttpProtocol.test(normalizedURL)) {
      throw new AxiosError$1(
        `Invalid URL ${JSON.stringify(redactSensitiveURLParts(normalizedURL))}: missing "//" after protocol`,
        AxiosError$1.ERR_INVALID_URL,
        config
      );
    }
  }
}

/**
 * Creates a new URL by combining the baseURL with the requestedURL,
 * only when the requestedURL is not already an absolute URL.
 * If the requestURL is absolute, this function returns the requestedURL untouched.
 *
 * @param {string} baseURL The base URL
 * @param {string} requestedURL Absolute or relative URL to combine
 *
 * @returns {string} The combined full path
 */
function buildFullPath(baseURL, requestedURL, allowAbsoluteUrls, config) {
  assertValidHttpProtocolURL(requestedURL, config);
  let isRelativeUrl = !isAbsoluteURL(requestedURL);
  if (baseURL && (isRelativeUrl || allowAbsoluteUrls === false)) {
    assertValidHttpProtocolURL(baseURL, config);
    return combineURLs(baseURL, requestedURL);
  }
  return requestedURL;
}

function assertParamsAcyclic(params) {
  const pending = [{ value: params }];
  const active = new WeakSet();
  const visited = new WeakSet();

  while (pending.length) {
    const { value, done } = pending.pop();
    if (!utils$1.isPlainObject(value) && !utils$1.isArray(value)) continue;
    if (done) {
      active.delete(value);
      continue;
    }
    if (active.has(value)) {
      throw new AxiosError$1(
        'Circular reference detected in params',
        AxiosError$1.ERR_BAD_OPTION_VALUE
      );
    }
    if (visited.has(value)) continue;
    visited.add(value);
    active.add(value);
    pending.push({ value, done: true });

    const keys = Object.keys(value);
    if (Object.getOwnPropertySymbols && Object.getOwnPropertyDescriptor) {
      Object.getOwnPropertySymbols(value).forEach((key) => {
        const descriptor = Object.getOwnPropertyDescriptor(value, key);
        if (descriptor && descriptor.enumerable) keys.push(key);
      });
    }
    // Shallow array elements retain fields filtered during plain-object merges.
    // Inspect reserved data properties without evaluating their accessors.
    keys.forEach((key) => {
      if (key === '__proto__' || key === 'constructor' || key === 'prototype') {
        const descriptor = Object.getOwnPropertyDescriptor(value, key);
        if (descriptor && utils$1.hasOwnProp(descriptor, 'value')) {
          pending.push({ value: descriptor.value });
        }
      } else {
        pending.push({ value: value[key] });
      }
    });
  }
}

const headersToObject = (thing) => (thing instanceof AxiosHeaders$1 ? { ...thing } : thing);

const ownEnumerableKeys = (thing) => {
  if (Object.getOwnPropertySymbols && Object.getOwnPropertyDescriptor) {
    return Object.keys(thing).concat(
      Object.getOwnPropertySymbols(thing).filter((symbol) => {
        const descriptor = Object.getOwnPropertyDescriptor(thing, symbol);
        return descriptor && descriptor.enumerable;
      })
    );
  }
  return Object.keys(thing);
};

// Copy params without recursive merges so the serializer remains responsible
// for its depth policy. Only visit defaults that contribute to the result.
function mergeParams(a, b) {
  const pending = [];
  const copies = new WeakMap();
  const empty = {};

  function copy(target, source) {
    if (!utils$1.isPlainObject(source)) {
      return utils$1.isArray(source) ? source.slice() : source;
    }

    const base = utils$1.isPlainObject(target) ? target : empty;
    let bases = copies.get(source);
    if (!bases) {
      bases = new WeakMap();
      copies.set(source, bases);
    }
    if (bases.has(base)) return bases.get(base);

    const result = {};
    bases.set(base, result);
    pending.push({ base, source, result });
    return result;
  }

  const result = utils$1.isUndefined(b) ? copy(undefined, a) : copy(a, b);
  while (pending.length) {
    const { base, source, result: target } = pending.pop();
    const baseKeys = new Set(ownEnumerableKeys(base));
    const sourceKeys = new Set(ownEnumerableKeys(source));
    const keys = new Set([...baseKeys, ...sourceKeys]);

    keys.forEach((key) => {
      if (key === '__proto__' || key === 'constructor' || key === 'prototype') return;
      const hasSource = sourceKeys.has(key);
      const value = hasSource ? source[key] : undefined;
      const previous =
        (!hasSource || utils$1.isPlainObject(value)) && baseKeys.has(key) ? base[key] : undefined;
      target[key] = hasSource ? copy(previous, value) : copy(undefined, previous);
    });
  }

  assertParamsAcyclic(result);
  return result;
}

function getMergedValue(target, source, prop, caseless) {
  if (utils$1.isPlainObject(target) && utils$1.isPlainObject(source)) {
    return utils$1.merge.call({ caseless }, target, source);
  } else if (utils$1.isPlainObject(source)) {
    return utils$1.merge({}, source);
  } else if (utils$1.isArray(source)) {
    return source.slice();
  }
  return source;
}

function mergeDeepProperties(a, b, prop, caseless) {
  if (!utils$1.isUndefined(b)) {
    return getMergedValue(a, b, prop, caseless);
  } else if (!utils$1.isUndefined(a)) {
    return getMergedValue(undefined, a, prop, caseless);
  }
}

// eslint-disable-next-line consistent-return
function valueFromConfig2(a, b) {
  if (!utils$1.isUndefined(b)) {
    return getMergedValue(undefined, b);
  }
}

// eslint-disable-next-line consistent-return
function defaultToConfig2(a, b) {
  if (!utils$1.isUndefined(b)) {
    return getMergedValue(undefined, b);
  } else if (!utils$1.isUndefined(a)) {
    return getMergedValue(undefined, a);
  }
}

function getMergedTransitionalOption(config1, config2, prop) {
  const transitional2 = utils$1.hasOwnProp(config2, 'transitional')
    ? config2.transitional
    : undefined;

  if (!utils$1.isUndefined(transitional2)) {
    if (utils$1.isPlainObject(transitional2)) {
      if (utils$1.hasOwnProp(transitional2, prop)) {
        return transitional2[prop];
      }
    } else {
      return undefined;
    }
  }

  const transitional1 = utils$1.hasOwnProp(config1, 'transitional')
    ? config1.transitional
    : undefined;

  if (utils$1.isPlainObject(transitional1) && utils$1.hasOwnProp(transitional1, prop)) {
    return transitional1[prop];
  }

  return undefined;
}

// eslint-disable-next-line consistent-return
function mergeDirectKeys(a, b, prop, config1, config2) {
  if (utils$1.hasOwnProp(config2, prop)) {
    return getMergedValue(a, b);
  } else if (utils$1.hasOwnProp(config1, prop)) {
    return getMergedValue(undefined, a);
  }
}

function mergeHeaders(a, b, prop) {
  return mergeDeepProperties(headersToObject(a), headersToObject(b), prop, true);
}

// Null-proto, frozen descriptor so a polluted Object.prototype.get cannot turn
// this data descriptor into an accessor descriptor on the way in.
// defineProperty only reads it, so one shared instance serves every call.
const hasOwnPropertyDescriptor = Object.freeze({
  __proto__: null,
  value: Object.prototype.hasOwnProperty,
  enumerable: false,
  writable: true,
  configurable: true,
});

// The strategy table and the strategies above are stateless, so they are
// built once at module load instead of on every call: mergeConfig runs at
// most twice per request (once from a method alias, once from `_request`).
const mergeMap = {
  url: valueFromConfig2,
  method: valueFromConfig2,
  data: valueFromConfig2,
  baseURL: defaultToConfig2,
  transformRequest: defaultToConfig2,
  transformResponse: defaultToConfig2,
  params: mergeParams,
  paramsSerializer: defaultToConfig2,
  timeout: defaultToConfig2,
  timeoutErrorMessage: defaultToConfig2,
  withCredentials: defaultToConfig2,
  withXSRFToken: defaultToConfig2,
  adapter: defaultToConfig2,
  responseType: defaultToConfig2,
  xsrfCookieName: defaultToConfig2,
  xsrfHeaderName: defaultToConfig2,
  onUploadProgress: defaultToConfig2,
  onDownloadProgress: defaultToConfig2,
  decompress: defaultToConfig2,
  maxContentLength: defaultToConfig2,
  maxBodyLength: defaultToConfig2,
  beforeRedirect: defaultToConfig2,
  transport: defaultToConfig2,
  httpAgent: defaultToConfig2,
  httpsAgent: defaultToConfig2,
  cancelToken: defaultToConfig2,
  socketPath: defaultToConfig2,
  allowedSocketPaths: defaultToConfig2,
  responseEncoding: defaultToConfig2,
  validateStatus: mergeDirectKeys,
  headers: mergeHeaders,
};

/**
 * Config-specific merge-function which creates a new config-object
 * by merging two configuration objects together.
 *
 * @param {Object} config1
 * @param {Object} config2
 *
 * @returns {Object} New object resulting from merging config2 to config1
 */
function mergeConfig(config1, config2) {
  // eslint-disable-next-line no-param-reassign
  config1 = config1 || {};
  config2 = config2 || {};

  // Use a null-prototype object so that downstream reads such as `config.auth`
  // or `config.baseURL` cannot inherit polluted values from Object.prototype.
  // `hasOwnProperty` is restored as a non-enumerable own slot to preserve
  // ergonomics for user code that relies on it.
  const config = Object.create(null);
  Object.defineProperty(config, 'hasOwnProperty', hasOwnPropertyDescriptor);

  const keys = ownEnumerableKeys({ ...config1, ...config2 });

  for (let i = 0, len = keys.length; i < len; i++) {
    const prop = keys[i];
    if (prop === '__proto__' || prop === 'constructor' || prop === 'prototype') continue;
    const merge = utils$1.hasOwnProp(mergeMap, prop) ? mergeMap[prop] : mergeDeepProperties;
    const a = utils$1.hasOwnProp(config1, prop) ? config1[prop] : undefined;
    const b = utils$1.hasOwnProp(config2, prop) ? config2[prop] : undefined;
    const configValue =
      merge === mergeDirectKeys ? merge(a, b, prop, config1, config2) : merge(a, b, prop);
    (utils$1.isUndefined(configValue) && merge !== mergeDirectKeys) || (config[prop] = configValue);
  }

  if (
    utils$1.hasOwnProp(config2, 'validateStatus') &&
    utils$1.isUndefined(config2.validateStatus) &&
    getMergedTransitionalOption(config1, config2, 'validateStatusUndefinedResolves') === false
  ) {
    if (utils$1.hasOwnProp(config1, 'validateStatus')) {
      config.validateStatus = getMergedValue(undefined, config1.validateStatus);
    } else {
      delete config.validateStatus;
    }
  }

  return config;
}

const FORM_DATA_CONTENT_HEADERS = ['content-type', 'content-length'];

/**
 * Apply the headers generated by a FormData implementation to the request headers,
 * honoring the `formDataHeaderPolicy` option: with 'content-only', copy only the
 * content-* headers; otherwise merge all of them.
 *
 * @param {AxiosHeaders} headers - the request headers to mutate
 * @param {Object | null | undefined} formHeaders - headers produced by the FormData implementation
 * @param {String} [policy] - the resolved `formDataHeaderPolicy` config value
 *
 * @returns {void}
 */
function setFormDataHeaders(headers, formHeaders, policy) {
  if (policy !== 'content-only') {
    headers.set(formHeaders);
    return;
  }

  Object.entries(formHeaders || {}).forEach(([key, val]) => {
    if (FORM_DATA_CONTENT_HEADERS.includes(key.toLowerCase())) {
      headers.set(key, val);
    }
  });
}

/**
 * Encode a UTF-8 string to a Latin-1 byte string for use with btoa().
 * This is a modern replacement for the deprecated unescape(encodeURIComponent(str)) pattern.
 *
 * @param {string} str The string to encode
 *
 * @returns {string} UTF-8 bytes as a Latin-1 string
 */
const encodeUTF8$1 = (str) =>
  encodeURIComponent(str).replace(/%([0-9A-F]{2})/gi, (_, hex) =>
    String.fromCharCode(parseInt(hex, 16))
  );

const readCookie = (name) => cookies.read(name);

function resolveConfig(config, readXsrfCookie = readCookie) {
  const newConfig = mergeConfig({}, config);

  // Read only own properties to prevent prototype pollution gadgets
  // (e.g. Object.prototype.baseURL = 'https://evil.com').
  const own = (key) => (utils$1.hasOwnProp(newConfig, key) ? newConfig[key] : undefined);

  const data = own('data');
  let withXSRFToken = own('withXSRFToken');
  const xsrfHeaderName = own('xsrfHeaderName');
  const xsrfCookieName = own('xsrfCookieName');
  let headers = own('headers');
  const auth = own('auth');
  const baseURL = own('baseURL');
  const allowAbsoluteUrls = own('allowAbsoluteUrls');
  const url = own('url');

  newConfig.headers = headers = AxiosHeaders$1.from(headers);

  newConfig.url = buildURL(
    buildFullPath(baseURL, url, allowAbsoluteUrls, newConfig),
    own('params'),
    own('paramsSerializer')
  );

  // HTTP basic authentication
  if (auth) {
    const username = utils$1.getSafeProp(auth, 'username') || '';
    const password = utils$1.getSafeProp(auth, 'password') || '';
    const transitional = own('transitional');
    const encodeUsername =
      transitional &&
      utils$1.hasOwnProp(transitional, 'encodeBasicAuthUsername') &&
      transitional.encodeBasicAuthUsername === true;

    try {
      headers.set(
        'Authorization',
        // Preserve legacy username bytes unless the caller opts in to UTF-8.
        'Basic ' +
          btoa(
            (encodeUsername ? encodeUTF8$1(username) : username) +
              ':' +
              (password ? encodeUTF8$1(password) : '')
          )
      );
    } catch (e) {
      throw AxiosError$1.from(e, AxiosError$1.ERR_BAD_OPTION_VALUE, config);
    }
  }

  if (utils$1.isFormData(data)) {
    const getHeaders = utils$1.getSafeProp(data, 'getHeaders');

    if (
      platform.hasStandardBrowserEnv ||
      platform.hasStandardBrowserWebWorkerEnv ||
      utils$1.isReactNative(data)
    ) {
      headers.setContentType(undefined); // browser/web worker/RN handles it
    } else if (utils$1.isFunction(getHeaders)) {
      // Node.js FormData (like form-data package)
      setFormDataHeaders(headers, getHeaders.call(data), own('formDataHeaderPolicy'));
    }
  }

  // Add xsrf header
  // This is only done if running in a standard browser environment.
  // Specifically not if we're in a web worker, or react-native.

  if (platform.hasStandardBrowserEnv) {
    if (utils$1.isFunction(withXSRFToken)) {
      withXSRFToken = withXSRFToken(newConfig);
    }

    // Strict boolean check — prevents proto-pollution gadgets (e.g. Object.prototype.withXSRFToken = 1)
    // and misconfigurations (e.g. "false") from short-circuiting the same-origin check and leaking
    // the XSRF token cross-origin.
    const shouldSendXSRF =
      withXSRFToken === true || (withXSRFToken == null && isURLSameOrigin(newConfig.url));

    if (shouldSendXSRF) {
      const xsrfValue = xsrfHeaderName && xsrfCookieName && readXsrfCookie(xsrfCookieName);

      if (xsrfValue) {
        headers.set(xsrfHeaderName, xsrfValue);
      }
    }
  }

  return newConfig;
}

const isXHRAdapterSupported = typeof XMLHttpRequest !== 'undefined';

const xhrAdapter = isXHRAdapterSupported &&
  function (config) {
    return new Promise(function dispatchXhrRequest(resolve, reject) {
      let useAsyncXsrf;
      try {
        const store =
          platform.hasStandardBrowserEnv && typeof window !== 'undefined' && window.cookieStore;
        useAsyncXsrf = store && utils$1.isFunction(store.get);
      } catch (e) {
        // A restricted Cookie Store getter must retain the synchronous fallback.
      }
      let xsrfCookieName;
      const _config = resolveConfig(
        config,
        useAsyncXsrf
          ? (name) => {
              xsrfCookieName = name;
              return null;
            }
          : undefined
      );
      let requestData = _config.data;
      const requestHeaders = AxiosHeaders$1.from(_config.headers).normalize();
      let { responseType, onUploadProgress, onDownloadProgress } = _config;
      let onCanceled;
      let timeoutId;
      let uploadThrottled, downloadThrottled;
      let flushUpload, flushDownload, flushDownloadWithEvent;

      function done() {
        clearTimeout(timeoutId);
        // A final progress callback must not prevent the remaining cleanup.
        // Report errors asynchronously, as onloadend and the throttle timer do.
        try {
          flushUpload && flushUpload(); // flush events
        } catch (err) {
          setTimeout(() => {
            throw err;
          });
        }
        try {
          flushDownload && flushDownload(); // flush events
        } catch (err) {
          setTimeout(() => {
            throw err;
          });
        }

        // A flush can synchronously cancel the request and reenter done().
        // In that case the inner call has already detached these listeners.
        if (request) {
          downloadThrottled && request.removeEventListener('progress', downloadThrottled);
          if (request.upload) {
            uploadThrottled && request.upload.removeEventListener('progress', uploadThrottled);
            flushUpload && request.upload.removeEventListener('loadend', flushUpload);
          }
        }

        _config.cancelToken && _config.cancelToken.unsubscribe(onCanceled);

        _config.signal && _config.signal.removeEventListener('abort', onCanceled);
      }

      let request = new XMLHttpRequest();

      request.open(_config.method.toUpperCase(), _config.url, true);

      // Set the request timeout in MS
      request.timeout = _config.timeout;

      function onloadend(event) {
        if (!request) {
          return;
        }

        // Status 0 means no response was received, which onerror and onabort normally
        // reject before this runs. Firefox 152 fires only readystatechange and loadend for
        // navigation-canceled requests (https://bugzilla.mozilla.org/show_bug.cgi?id=1505389),
        // leaving settle() to resolve them as an empty success. ECONNABORTED is the error
        // onabort raised on Firefox 151. Reads over file:, which some environments report as
        // status 0 on success, are excluded by the request URL's scheme after browser-style
        // preprocessing, by the page origin's scheme for relative URLs (which inherit it), or
        // by responseURL where implemented.
        if (
          request.status === 0 &&
          (parseProtocol(normalizeURLForProtocolCheck(_config.url)) ||
            parseProtocol(platform.origin)) !== 'file' &&
          !(request.responseURL && request.responseURL.startsWith('file:'))
        ) {
          reject(new AxiosError$1('Request aborted', AxiosError$1.ECONNABORTED, config, request));
          done();

          // Clean up request
          request = null;
          return;
        }

        // When loadend is still dispatching, flushing with it gives progress
        // listeners a final delivery whose event has a live target. The legacy
        // ready-state fallback has no event, so replay its pending progress.
        // A throwing listener must not block settlement; rethrow asynchronously,
        // matching how listener errors surface on the throttle timer path.
        try {
          if (event) {
            flushDownloadWithEvent && flushDownloadWithEvent(event);
          } else {
            flushDownload && flushDownload();
          }
        } catch (err) {
          setTimeout(() => {
            throw err;
          });
        }

        // A final progress callback can cancel the request synchronously.
        if (!request) {
          return;
        }

        // Prepare the response
        const responseHeaders = AxiosHeaders$1.from(
          'getAllResponseHeaders' in request && request.getAllResponseHeaders()
        );
        const responseData =
          !responseType || responseType === 'text' || responseType === 'json'
            ? request.responseText
            : request.response;
        const response = {
          data: responseData,
          status: request.status,
          statusText: request.statusText,
          headers: responseHeaders,
          config,
          request,
        };

        settle(
          function _resolve(value) {
            resolve(value);
            done();
          },
          function _reject(err) {
            reject(err);
            done();
          },
          response
        );

        // Clean up request
        request = null;
      }

      if ('onloadend' in request) {
        // Use onloadend if available
        request.onloadend = onloadend;
      } else {
        // Listen for ready state to emulate onloadend
        request.onreadystatechange = function handleLoad() {
          if (!request || request.readyState !== 4) {
            return;
          }

          // The request errored out and we didn't get a response, this will be
          // handled by onerror instead
          // With one exception: request that using file: protocol, most browsers
          // will return status as 0 even though it's a successful request
          if (
            request.status === 0 &&
            !(request.responseURL && request.responseURL.startsWith('file:'))
          ) {
            return;
          }
          // readystate handler is calling before onerror or ontimeout handlers,
          // so we should call onloadend on the next 'tick'
          setTimeout(onloadend);
        };
      }

      // Handle browser request cancellation (as opposed to a manual cancellation)
      request.onabort = function handleAbort() {
        if (!request) {
          return;
        }

        reject(new AxiosError$1('Request aborted', AxiosError$1.ECONNABORTED, config, request));
        done();

        // Clean up request
        request = null;
      };

      // Handle low level network errors
      request.onerror = function handleError(event) {
        // Browsers deliver a ProgressEvent in XHR onerror
        // (message may be empty; when present, surface it)
        // See https://developer.mozilla.org/docs/Web/API/XMLHttpRequest/error_event
        const msg = event && event.message ? event.message : 'Network Error';
        const err = new AxiosError$1(msg, AxiosError$1.ERR_NETWORK, config, request);
        // attach the underlying event for consumers who want details
        err.event = event || null;
        reject(err);
        done();
        request = null;
      };

      // Handle timeout
      request.ontimeout = function handleTimeout() {
        if (!request) return;
        let timeoutErrorMessage = _config.timeout
          ? 'timeout of ' + _config.timeout + 'ms exceeded'
          : 'timeout exceeded';
        const transitional = _config.transitional || transitionalDefaults;
        if (_config.timeoutErrorMessage) {
          timeoutErrorMessage = _config.timeoutErrorMessage;
        }
        reject(
          new AxiosError$1(
            timeoutErrorMessage,
            transitional.clarifyTimeoutError ? AxiosError$1.ETIMEDOUT : AxiosError$1.ECONNABORTED,
            config,
            request
          )
        );
        done();

        // Clean up request
        request = null;
      };

      // Remove Content-Type if data is undefined
      requestData === undefined && requestHeaders.setContentType(null);

      // Add withCredentials to request if needed
      if (!utils$1.isUndefined(_config.withCredentials)) {
        request.withCredentials = !!_config.withCredentials;
      }

      // Add responseType to request if needed
      if (responseType && responseType !== 'json') {
        request.responseType = _config.responseType;
      }

      // Handle progress if needed
      if (onDownloadProgress) {
        [downloadThrottled, flushDownload, flushDownloadWithEvent] = progressEventReducer(
          onDownloadProgress,
          true
        );
        request.addEventListener('progress', downloadThrottled);
      }

      // Not all browsers support upload events
      if (onUploadProgress && request.upload) {
        [uploadThrottled, flushUpload] = progressEventReducer(onUploadProgress);

        request.upload.addEventListener('progress', uploadThrottled);

        request.upload.addEventListener('loadend', flushUpload);
      }

      if (_config.cancelToken || _config.signal) {
        // Handle cancellation
        // eslint-disable-next-line func-names
        onCanceled = (cancel) => {
          if (!request) {
            return;
          }
          reject(!cancel || cancel.type ? new CanceledError$1(null, config, request) : cancel);
          const xhr = request;
          done();
          request = null;
          xhr.abort();
        };

        _config.cancelToken && _config.cancelToken.subscribe(onCanceled);
        if (!request) return;
        if (_config.signal) {
          _config.signal.aborted
            ? onCanceled()
            : _config.signal.addEventListener('abort', onCanceled);
        }
      }

      if (!request) return;

      const protocol = parseProtocol(_config.url);

      if (protocol && !platform.protocols.includes(protocol)) {
        reject(
          new AxiosError$1(
            'Unsupported protocol ' + protocol + ':',
            AxiosError$1.ERR_BAD_REQUEST,
            config
          )
        );
        done();
        return;
      }

      const sendRequest = () => {
        if (!request) return;
        // Apply headers after an asynchronous XSRF read so existing headers are
        // replaced through AxiosHeaders rather than appended by the native XHR.
        if ('setRequestHeader' in request) {
          utils$1.forEach(
            toByteStringHeaderObject(requestHeaders),
            function setRequestHeader(val, key) {
              request.setRequestHeader(key, val);
            }
          );
        }
        request.send(requestData || null);
      };

      if (xsrfCookieName) {
        // Native XHR timeout starts at send(). Cover cookie preparation and the
        // subsequent request with the same budget and existing timeout handler.
        const now =
          typeof performance !== 'undefined' && utils$1.isFunction(performance.now)
            ? () => performance.now()
            : Date.now;
        const deadline = request.timeout > 0 ? now() + Number(request.timeout) : undefined;
        const abortOnTimeout = () => {
          if (!request) return;
          const xhr = request;
          xhr.ontimeout();
          xhr.abort();
        };
        if (deadline !== undefined) {
          const scheduleTimeout = () => {
            const remaining = deadline - now();
            if (remaining > 0) {
              // Browser timers overflow above the signed 32-bit delay limit.
              timeoutId = setTimeout(scheduleTimeout, Math.min(remaining, 0x7fffffff));
            } else {
              abortOnTimeout();
            }
          };
          scheduleTimeout();
        }

        cookies
          .readAsync(xsrfCookieName)
          .then((value) => {
            if (!request) return;
            // Promise callbacks may run before an overdue timer after a busy task.
            if (deadline !== undefined && now() >= deadline) {
              abortOnTimeout();
              return;
            }
            if (value) {
              const headerName =
                utils$1.hasOwnProp(_config, 'xsrfHeaderName') && _config.xsrfHeaderName;
              requestHeaders.set(headerName, value);
            }
            sendRequest();
          })
          .catch((error) => {
            if (!request) return;
            reject(AxiosError$1.from(error, null, config, request));
            done();
            request = null;
          });
      } else {
        sendRequest();
      }
    });
  };

const composeSignals = (signals, timeout) => {
  signals = signals ? signals.filter(Boolean) : [];

  if (!timeout && !signals.length) {
    return;
  }

  const controller = new AbortController();

  let aborted = false;

  const onabort = function (reason) {
    if (!aborted) {
      aborted = true;
      unsubscribe();
      const err = reason instanceof Error ? reason : this.reason;
      controller.abort(
        err instanceof AxiosError$1
          ? err
          : new CanceledError$1(err instanceof Error ? err.message : err)
      );
    }
  };

  let timer =
    timeout &&
    setTimeout(() => {
      timer = null;
      onabort(new AxiosError$1(`timeout of ${timeout}ms exceeded`, AxiosError$1.ETIMEDOUT));
    }, timeout);

  const unsubscribe = () => {
    if (!signals) {
      return;
    }
    timer && clearTimeout(timer);
    timer = null;
    signals.forEach((signal) => {
      const unsubscribeSignal = utils$1.getSafeProp(signal, 'unsubscribe');
      utils$1.isFunction(unsubscribeSignal)
        ? unsubscribeSignal.call(signal, onabort)
        : signal.removeEventListener('abort', onabort);
    });
    signals = null;
  };

  signals.forEach((signal) => {
    if (aborted) {
      return;
    }

    if (signal.aborted) {
      onabort.call(signal);
      return;
    }

    signal.addEventListener('abort', onabort, { once: true });
  });

  const { signal } = controller;

  signal.unsubscribe = () => utils$1.asap(unsubscribe);

  return signal;
};

const composeSignals$1 = composeSignals;

const streamChunk = function* (chunk, chunkSize) {
  let len = chunk.byteLength;

  if (!chunkSize || len < chunkSize) {
    yield chunk;
    return;
  }

  let pos = 0;
  let end;

  while (pos < len) {
    end = pos + chunkSize;
    yield chunk.slice(pos, end);
    pos = end;
  }
};

const readBytes = async function* (iterable, chunkSize) {
  for await (const chunk of readStream(iterable)) {
    yield* streamChunk(chunk, chunkSize);
  }
};

const readStream = async function* (stream) {
  if (stream[Symbol.asyncIterator]) {
    yield* stream;
    return;
  }

  const reader = stream.getReader();
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      yield value;
    }
  } finally {
    await reader.cancel();
  }
};

const trackStream = (stream, chunkSize, onProgress, onFinish) => {
  const iterator = readBytes(stream, chunkSize);

  let bytes = 0;
  let done;
  let _onFinish = (e) => {
    if (!done) {
      done = true;
      onFinish && onFinish(e);
    }
  };

  return new ReadableStream(
    {
      async pull(controller) {
        try {
          const { done, value } = await iterator.next();

          if (done) {
            _onFinish();
            controller.close();
            return;
          }

          let len = value.byteLength;
          if (onProgress) {
            let loadedBytes = (bytes += len);
            onProgress(loadedBytes);
          }
          controller.enqueue(new Uint8Array(value));
        } catch (err) {
          _onFinish(err);
          throw err;
        }
      },
      cancel(reason) {
        _onFinish(reason);
        return iterator.return();
      },
    },
    {
      highWaterMark: 2,
    }
  );
};

const CRLF = '\r\n';
const normalizeLines = (value) => String(value).replace(/\r\n|\r|\n/g, CRLF);
const escapeName = (value) =>
  String(value).replace(/[\r\n"]/g, (char) =>
    char === '\r' ? '%0D' : char === '\n' ? '%0A' : '%22'
  );

// Count UTF-8 bytes without allocating an encoded copy of a field. FormData
// string values normalize line endings; Blob/File contents remain unchanged.
const stringBytes = (value, normalize) => {
  let length = 0;
  for (let i = 0; i < value.length; i++) {
    const code = value.charCodeAt(i);
    if (normalize && (code === 13 || code === 10)) {
      if (code === 13 && value.charCodeAt(i + 1) === 10) i++;
      length += 2;
    } else if (code < 0x80) {
      length++;
    } else if (code < 0x800) {
      length += 2;
    } else if (
      code >= 0xd800 &&
      code <= 0xdbff &&
      value.charCodeAt(i + 1) >= 0xdc00 &&
      value.charCodeAt(i + 1) <= 0xdfff
    ) {
      length += 4;
      i++;
    } else {
      length += 3;
    }
  }
  return length;
};

// Describe serialization failures independently of any request library.
class FormDataError extends TypeError {
  constructor(message, reason) {
    super(message);
    this.name = 'FormDataError';
    this.reason = reason;
  }
}

// The caller supplies the boundary, Blob implementation, and limit error.
function formDataToBlob(form, Blob, limit, limitError, boundary) {
  if (!utils$1.isFunction(Blob)) {
    throw new FormDataError('Blob is not supported', 'blob');
  }

  if (
    !utils$1.isString(boundary) ||
    !/^[A-Za-z0-9'()+_,./:=? -]{1,70}$/.test(boundary) ||
    / $/.test(boundary)
  ) {
    throw new FormDataError('Invalid multipart boundary', 'boundary');
  }
  const footer = '--' + boundary + '--' + CRLF;
  let length = footer.length;
  const parts = [];
  const checkLength = (extra) => {
    if (length + extra > limit) throw limitError();
  };
  checkLength(0);

  for (const [name, value] of form) {
    const isString = utils$1.isString(value);
    const valueLength = isString ? stringBytes(value, true) : value.size;
    if (!Number.isFinite(valueLength) || valueLength < 0) {
      throw new FormDataError('Unsupported FormData part size', 'part');
    }
    // Reject large values and names before building normalized header strings.
    checkLength(
      valueLength +
        stringBytes(name, true) +
        (!isString && value.name ? stringBytes(value.name, false) : 0) +
        (!isString && value.type ? stringBytes(value.type, false) : 0)
    );

    let header =
      '--' +
      boundary +
      CRLF +
      'Content-Disposition: form-data; name="' +
      escapeName(normalizeLines(name)) +
      '"';
    if (!isString) {
      header +=
        '; filename="' +
        escapeName(utils$1.isString(value.name) ? value.name : 'blob') +
        '"' +
        CRLF +
        'Content-Type: ' +
        String(value.type || 'application/octet-stream').replace(/[\r\n]/g, '');
    }
    header += CRLF + CRLF;
    const partLength = stringBytes(header, false) + valueLength + CRLF.length;
    checkLength(partLength);
    length += partLength;
    parts.push({ header, value, isString });
  }

  // Native Blob composition retains existing Blob/File data. No file is read
  // and no complete multipart ArrayBuffer is created to determine its length.
  const blobParts = [];
  for (const part of parts) {
    blobParts.push(part.header, part.isString ? normalizeLines(part.value) : part.value, CRLF);
  }
  blobParts.push(footer);
  return new Blob(blobParts, { type: 'multipart/form-data; boundary=' + boundary });
}

function createMultipartBody(form, Blob, limit, limitError, boundary) {
  // Report missing Blob support before trying to select a random source.
  if (!utils$1.isFunction(Blob)) {
    throw new AxiosError$1('Blob is not supported', AxiosError$1.ERR_NOT_SUPPORT);
  }

  if (boundary === undefined) {
    if (utils$1.isFunction(platform.generateString)) {
      boundary = 'axios-' + platform.generateString(36, '0123456789abcdef');
    } else {
      const crypto = utils$1.global.crypto;
      if (!crypto || !utils$1.isFunction(crypto.getRandomValues)) {
        throw new AxiosError$1('Random byte generation is not supported', AxiosError$1.ERR_NOT_SUPPORT);
      }
      const random = new Uint8Array(18);
      crypto.getRandomValues(random);
      boundary =
        'axios-' + Array.from(random, (value) => ('0' + value.toString(16)).slice(-2)).join('');
    }
  }

  try {
    return formDataToBlob(form, Blob, limit, limitError, boundary);
  } catch (error) {
    if (error instanceof FormDataError) {
      const code =
        error.reason === 'boundary' ? AxiosError$1.ERR_BAD_OPTION_VALUE : AxiosError$1.ERR_BAD_REQUEST;
      throw new AxiosError$1(error.message, code);
    }
    throw error;
  }
}

/**
 * Estimate data: URL byte lengths *without* allocating large buffers.
 * - Fetch percent-decodes a base64 body before decoding it.
 * - Node's Buffer.from(body, 'base64') sizes its backing allocation from the
 *   percent-decoded body, including ignored characters and content after padding.
 * - Non-base64 data is percent-decoded and then encoded as UTF-8.
 */
const isHexDigit = (charCode) =>
  (charCode >= 48 && charCode <= 57) ||
  (charCode >= 65 && charCode <= 70) ||
  (charCode >= 97 && charCode <= 102);

const isPercentEncodedByte = (str, i, len) =>
  i + 2 < len && isHexDigit(str.charCodeAt(i + 1)) && isHexDigit(str.charCodeAt(i + 2));

const hexValue = (charCode) => (charCode <= 57 ? charCode - 48 : (charCode & 0xdf) - 55);

const isBase64Char = (charCode) =>
  (charCode >= 65 && charCode <= 90) || // A-Z
  (charCode >= 97 && charCode <= 122) || // a-z
  (charCode >= 48 && charCode <= 57) || // 0-9
  charCode === 43 || // +
  charCode === 47 || // /
  charCode === 45 || // - (base64url)
  charCode === 95; // _ (base64url)

const isBase64Whitespace = (charCode) =>
  charCode === 9 || charCode === 10 || charCode === 12 || charCode === 13 || charCode === 32;

const base64Bytes = (significant) => {
  const groups = Math.floor(significant / 4);
  const remainder = significant % 4;
  return groups * 3 + (remainder === 2 ? 1 : remainder === 3 ? 2 : 0);
};

// Buffer.byteLength(body, 'base64') uses the raw string length as an allocation
// upper bound even when Buffer.from later ignores characters or stops at '='.
const estimateBase64BufferAllocation = (body) => {
  const len = body.length;
  let padding = 0;

  if (len > 0 && body.charCodeAt(len - 1) === 61 /* '=' */) {
    padding++;

    if (len > 1 && body.charCodeAt(len - 2) === 61 /* '=' */) {
      padding++;
    }
  }

  return Math.floor(((len - padding) * 3) / 4);
};

const estimatePercentDecodedBase64Bytes = (body) => {
  const len = body.length;
  let significant = 0;
  let padding = 0;
  let invalid = false;

  for (let i = 0; i < len; i++) {
    let code = body.charCodeAt(i);

    if (code === 37 /* '%' */ && isPercentEncodedByte(body, i, len)) {
      code = hexValue(body.charCodeAt(i + 1)) * 16 + hexValue(body.charCodeAt(i + 2));
      i += 2;
    }

    if (isBase64Whitespace(code)) {
      continue;
    }

    if (code === 61 /* '=' */) {
      padding++;
      continue;
    }

    if (!isBase64Char(code) || padding > 0) {
      invalid = true;
      continue;
    }

    significant++;
  }

  // Fetch rejects malformed forgiving-base64 input. Returning the raw-size
  // allocation bound keeps that invalid input from becoming a pre-check bypass.
  if (
    invalid ||
    padding > 2 ||
    (padding > 0 && (significant + padding) % 4 !== 0) ||
    significant % 4 === 1
  ) {
    return estimateBase64BufferAllocation(body);
  }

  return base64Bytes(significant);
};

const estimateDataURLBytes = (url, estimateBase64, base64Pattern) => {
  if (!url || typeof url !== 'string') return 0;
  if (!/^data:/i.test(url)) return 0;

  const comma = url.indexOf(',');
  if (comma < 0) return 0;

  const meta = url.slice(5, comma);
  const body = url.slice(comma + 1);
  const isBase64 = base64Pattern.test(meta);

  if (isBase64) {
    return estimateBase64(body);
  }

  // Compute UTF-8 byte length directly from UTF-16 code units without allocating
  // a byte buffer (TextEncoder.encode would defeat the DoS guard on large bodies).
  // Valid %XX triplets count as one decoded byte; this matches the bytes that
  // decodeURIComponent(body) would produce before Buffer re-encodes the string.
  let bytes = 0;
  for (let i = 0, len = body.length; i < len; i++) {
    const c = body.charCodeAt(i);
    if (c === 37 /* '%' */ && isPercentEncodedByte(body, i, len)) {
      bytes += 1;
      i += 2;
    } else if (c < 0x80) {
      bytes += 1;
    } else if (c < 0x800) {
      bytes += 2;
    } else if (c >= 0xd800 && c <= 0xdbff && i + 1 < len) {
      const next = body.charCodeAt(i + 1);
      if (next >= 0xdc00 && next <= 0xdfff) {
        bytes += 4;
        i++;
      } else {
        bytes += 3;
      }
    } else {
      bytes += 3;
    }
  }
  return bytes;
};

/**
 * Estimate the percent-decoded payload size used by Fetch data: URLs.
 *
 * @param {string} url
 * @returns {number}
 */
function estimateDataURLDecodedBytes(url) {
  // Fetch removes URL fragments before processing a data: URL.
  const fragmentIndex = typeof url === 'string' ? url.indexOf('#') : -1;

  return estimateDataURLBytes(
    fragmentIndex === -1 ? url : url.slice(0, fragmentIndex),
    estimatePercentDecodedBase64Bytes,
    /; *base64[\t\n\f\r ]*$/i
  );
}

const VERSION = "1.21.0";

const DEFAULT_CHUNK_SIZE = 64 * 1024;

const DEFAULT_REQUEST_OPTIONS = {
  cache: 'default',
  redirect: 'follow',
  referrer: 'about:client',
  referrerPolicy: '',
  mode: 'cors',
  integrity: '',
  keepalive: false,
  priority: 'auto',
  window: null,
};

const { isFunction } = utils$1;

/**
 * Encode a UTF-8 string to a Latin-1 byte string for use with btoa().
 * This is a modern replacement for the deprecated unescape(encodeURIComponent(str)) pattern.
 *
 * @param {string} str The string to encode
 *
 * @returns {string} UTF-8 bytes as a Latin-1 string
 */
const encodeUTF8 = (str) =>
  encodeURIComponent(str).replace(/%([0-9A-F]{2})/gi, (_, hex) =>
    String.fromCharCode(parseInt(hex, 16))
  );

// Node's WHATWG URL parser returns `username` and `password` percent-encoded.
// Decode before composing the `auth` option so credentials such as
// `my%40email.com:pass` are sent as `my@email.com:pass`. Falls back to the
// original value for malformed input so a bad encoding never throws.
const decodeURIComponentSafe = (value) => {
  if (!utils$1.isString(value)) {
    return value;
  }

  try {
    return decodeURIComponent(value);
  } catch (error) {
    return value;
  }
};

const test = (fn, ...args) => {
  try {
    return !!fn(...args);
  } catch (e) {
    return false;
  }
};

const maybeWithAuthCredentials = (url) => {
  const protocolIndex = url.indexOf('://');
  let urlToCheck = url;
  if (protocolIndex !== -1) {
    urlToCheck = urlToCheck.slice(protocolIndex + 3);
  }
  return urlToCheck.includes('@') || urlToCheck.includes(':');
};

const factory = (env) => {
  const globalObject =
    utils$1.global !== undefined && utils$1.global !== null ? utils$1.global : globalThis;
  const { ReadableStream, TextEncoder } = globalObject;

  env = utils$1.merge.call(
    {
      skipUndefined: true,
    },
    {
      Request: globalObject.Request,
      Response: globalObject.Response,
      Blob: globalObject.Blob,
    },
    env
  );

  const envFetch = utils$1.hasOwnProp(env, 'fetch') ? env.fetch : undefined;
  const { Request, Response, Blob } = env;
  const isFetchSupported = envFetch ? isFunction(envFetch) : typeof fetch === 'function';
  const isRequestSupported = isFunction(Request);
  const isResponseSupported = isFunction(Response);

  if (!isFetchSupported) {
    return false;
  }

  const isReadableStreamSupported = isFetchSupported && isFunction(ReadableStream);

  const encodeText =
    isFetchSupported &&
    (typeof TextEncoder === 'function'
      ? (
          (encoder) => (str) =>
            encoder.encode(str)
        )(new TextEncoder())
      : async (str) => new Uint8Array(await new Request(str).arrayBuffer()));

  const supportsRequestStream =
    isRequestSupported &&
    isReadableStreamSupported &&
    test(() => {
      let duplexAccessed = false;

      const request = new Request(platform.origin, {
        body: new ReadableStream(),
        method: 'POST',
        get duplex() {
          duplexAccessed = true;
          return 'half';
        },
      });

      const hasContentType = request.headers.has('Content-Type');

      if (request.body != null) {
        request.body.cancel();
      }

      return duplexAccessed && !hasContentType;
    });

  const supportsResponseStream =
    isResponseSupported &&
    isReadableStreamSupported &&
    test(() => utils$1.isReadableStream(new Response('').body));

  // Some runtimes reject every explicit cache mode. Use own defaults for both
  // probes so unrelated polluted options cannot affect cache-mode detection.
  const requestDefaults = Object.assign(Object.create(null), DEFAULT_REQUEST_OPTIONS);

  if (isRequestSupported && !test(() => new Request(platform.origin, requestDefaults))) {
    delete requestDefaults.cache;

    // Only omit cache when that makes Request construction succeed. Otherwise
    // retain the explicit default that protects supporting runtimes from pollution.
    if (!test(() => new Request(platform.origin, requestDefaults))) {
      requestDefaults.cache = DEFAULT_REQUEST_OPTIONS.cache;
    }
  }

  const resolvers = {
    stream: supportsResponseStream && ((res) => res.body),
  };

  isFetchSupported &&
    (() => {
      ['text', 'arrayBuffer', 'blob', 'formData', 'stream'].forEach((type) => {
        !resolvers[type] &&
          (resolvers[type] = (res, config) => {
            let method = res && res[type];

            if (method) {
              return method.call(res);
            }

            throw new AxiosError$1(
              `Response type '${type}' is not supported`,
              AxiosError$1.ERR_NOT_SUPPORT,
              config
            );
          });
      });
    })();

  const getBodyLength = async (body) => {
    if (body == null) {
      return 0;
    }

    if (utils$1.isBlob(body)) {
      return body.size;
    }

    if (utils$1.isArrayBufferView(body) || utils$1.isArrayBuffer(body)) {
      return body.byteLength;
    }

    if (utils$1.isURLSearchParams(body)) {
      body = body + '';
    }

    if (utils$1.isString(body)) {
      return (await encodeText(body)).byteLength;
    }
  };

  const resolveBodyLength = async (headers, body) => {
    const length = utils$1.toFiniteNumber(headers.getContentLength());

    return length == null ? getBodyLength(body) : length;
  };

  return async (config) => {
    let {
      url,
      method,
      data,
      signal,
      cancelToken,
      timeout,
      onDownloadProgress,
      onUploadProgress,
      responseType,
      headers,
      withCredentials = 'same-origin',
      fetchOptions,
      maxContentLength,
      maxBodyLength,
      maxRedirects,
    } = resolveConfig(config);

    const hasMaxContentLength = utils$1.isNumber(maxContentLength) && maxContentLength > -1;
    const hasMaxBodyLength = utils$1.isNumber(maxBodyLength) && maxBodyLength > -1;
    const own = (key) => (utils$1.hasOwnProp(config, key) ? config[key] : undefined);

    let _fetch = envFetch || fetch;

    responseType = responseType ? (responseType + '').toLowerCase() : 'text';

    let composedSignal = composeSignals$1(
      [signal, cancelToken && cancelToken.toAbortSignal()],
      timeout
    );

    let request = null;

    const unsubscribe =
      composedSignal &&
      composedSignal.unsubscribe &&
      (() => {
        composedSignal.unsubscribe();
      });

    let requestContentLength;

    // AxiosErrors we raise while request or response bodies are being streamed. Captured
    // by identity so the catch block can surface it directly, regardless of
    // how the runtime wraps the resulting fetch rejection (undici exposes it
    // as `err.cause`; some browsers drop the original error entirely).
    let pendingBodyError = null;
    let pendingResponseError = null;

    const maxBodyLengthError = () =>
      new AxiosError$1(
        'Request body larger than maxBodyLength limit',
        AxiosError$1.ERR_BAD_REQUEST,
        config,
        request
      );

    try {
      // HTTP basic authentication
      let auth = undefined;
      const configAuth = own('auth');

      if (configAuth) {
        const username = utils$1.getSafeProp(configAuth, 'username') || '';
        const password = utils$1.getSafeProp(configAuth, 'password') || '';
        auth = {
          username,
          password,
        };
      }

      let parsedURL;
      if (maybeWithAuthCredentials(url)) {
        parsedURL = new URL(url, platform.origin);

        if (!auth && (parsedURL.username || parsedURL.password)) {
          const urlUsername = decodeURIComponentSafe(parsedURL.username);
          const urlPassword = decodeURIComponentSafe(parsedURL.password);
          auth = {
            username: urlUsername,
            password: urlPassword,
          };
        }

        if (parsedURL.username || parsedURL.password) {
          parsedURL.username = '';
          parsedURL.password = '';
          url = parsedURL.href;
        }
      }

      if (auth) {
        headers.delete('authorization');
        headers.set(
          'Authorization',
          'Basic ' + btoa(encodeUTF8((auth.username || '') + ':' + (auth.password || '')))
        );
      }

      // Enforce maxContentLength for data: URLs up-front so we never materialize
      // an oversized payload. The HTTP adapter applies the same check (see http.js
      // "if (protocol === 'data:')" branch).
      if (hasMaxContentLength && parsedURL && parsedURL.protocol === 'data:') {
        const estimated = estimateDataURLDecodedBytes(parsedURL.href);
        if (estimated > maxContentLength) {
          throw new AxiosError$1(
            'maxContentLength size of ' + maxContentLength + ' exceeded',
            AxiosError$1.ERR_BAD_RESPONSE,
            config,
            request
          );
        }
      }

      const formContentType =
        utils$1.isSpecCompliantForm(data) && AxiosHeaders$1.from(own('headers')).getContentType();
      let formBoundary;
      if (
        utils$1.isString(formContentType) &&
        /^multipart\/form-data(?:\s*;|$)/i.test(formContentType.trim())
      ) {
        const parameters = AxiosHeaders$1.parseParameters(formContentType);
        if (utils$1.hasOwnProp(parameters, 'boundary')) formBoundary = parameters.boundary;
      }

      if (
        utils$1.isSpecCompliantForm(data) &&
        method !== 'get' &&
        method !== 'head' &&
        (hasMaxBodyLength ||
          (onUploadProgress && supportsRequestStream) ||
          formBoundary !== undefined)
      ) {
        data = createMultipartBody(
          data,
          Blob,
          hasMaxBodyLength ? maxBodyLength : Infinity,
          maxBodyLengthError,
          formBoundary
        );
        // Blob.type lowercases its value, including a case-sensitive boundary.
        // Retain the caller's header when an explicit boundary was serialized.
        headers.setContentType(formBoundary === undefined ? data.type : formContentType);
        requestContentLength = data.size;
      }

      // Enforce maxBodyLength against known-size bodies before dispatch using
      // the body's *actual* size — never a caller-declared Content-Length,
      // which could under-report to slip an oversized body past the check.
      // Unknown-size streams return undefined here and are counted per-chunk
      // below as fetch consumes them.
      if (hasMaxBodyLength && method !== 'get' && method !== 'head') {
        const outboundLength = await getBodyLength(data);
        if (typeof outboundLength === 'number' && isFinite(outboundLength)) {
          requestContentLength = outboundLength;
          if (outboundLength > maxBodyLength) {
            throw maxBodyLengthError();
          }
        }
      }

      // A streamed body under maxBodyLength must be counted as fetch consumes
      // it; its size is never trusted from a caller-declared Content-Length.
      const mustEnforceStreamBody =
        hasMaxBodyLength && (utils$1.isReadableStream(data) || utils$1.isStream(data));

      const trackRequestStream = (stream, onProgress, flush) =>
        trackStream(
          stream,
          DEFAULT_CHUNK_SIZE,
          (loadedBytes) => {
            if (hasMaxBodyLength && loadedBytes > maxBodyLength) {
              throw (pendingBodyError = maxBodyLengthError());
            }
            onProgress && onProgress(loadedBytes);
          },
          flush
        );

      if (
        supportsRequestStream &&
        method !== 'get' &&
        method !== 'head' &&
        (onUploadProgress || mustEnforceStreamBody)
      ) {
        requestContentLength =
          requestContentLength == null
            ? await resolveBodyLength(headers, data)
            : requestContentLength;

        // A declared length of 0 is only trusted to skip the wrap when we are
        // not enforcing a stream limit (which must not rely on that header).
        if (requestContentLength !== 0 || mustEnforceStreamBody) {
          let _request = new Request(url, {
            method: 'POST',
            body: data,
            duplex: 'half',
          });

          let contentTypeHeader;

          if (
            utils$1.isFormData(data) &&
            (contentTypeHeader = _request.headers.get('content-type'))
          ) {
            headers.setContentType(contentTypeHeader);
          }

          if (_request.body) {
            const [onProgress, flush] =
              (onUploadProgress &&
                progressEventDecorator(
                  requestContentLength,
                  progressEventReducer(asyncDecorator(onUploadProgress))
                )) ||
              [];

            data = trackRequestStream(_request.body, onProgress, flush);
          }
        }
      } else if (
        mustEnforceStreamBody &&
        !isRequestSupported &&
        isReadableStreamSupported &&
        method !== 'get' &&
        method !== 'head'
      ) {
        data = trackRequestStream(data);
      } else if (
        mustEnforceStreamBody &&
        isRequestSupported &&
        !supportsRequestStream &&
        method !== 'get' &&
        method !== 'head'
      ) {
        throw new AxiosError$1(
          'Stream request bodies are not supported by the current fetch implementation',
          AxiosError$1.ERR_NOT_SUPPORT,
          config,
          request
        );
      }

      if (!utils$1.isString(withCredentials)) {
        withCredentials = withCredentials ? 'include' : 'omit';
      }

      // Cloudflare Workers throws when credentials are defined
      // see https://github.com/cloudflare/workerd/issues/902
      const isCredentialsSupported = isRequestSupported && 'credentials' in Request.prototype;

      // If data is FormData and Content-Type is multipart/form-data without boundary,
      // delete it so fetch can set it correctly with the boundary
      if (utils$1.isFormData(data)) {
        const contentType = headers.getContentType();
        if (
          contentType &&
          /^multipart\/form-data/i.test(contentType) &&
          !/boundary=/i.test(contentType)
        ) {
          headers.delete('content-type');
        }
      }

      // Set User-Agent header if not already set (fetch defaults to 'node' in Node.js)
      headers.set('User-Agent', 'axios/' + VERSION, false);

      const safeFetchOptions =
        fetchOptions == null ? fetchOptions : Object.assign(Object.create(null), fetchOptions);

      if (safeFetchOptions) {
        // These options are owned by Axios and are already reflected in the
        // resolved Request passed to fetch.
        delete safeFetchOptions.body;
        delete safeFetchOptions.headers;
        delete safeFetchOptions.method;
        delete safeFetchOptions.signal;
        delete safeFetchOptions.duplex;
        delete safeFetchOptions.credentials;
      }

      const resolvedOptions = Object.assign(Object.create(null), safeFetchOptions, {
        signal: composedSignal,
        method: method.toUpperCase(),
        headers: toByteStringHeaderObject(headers.normalize()),
        body: data,
        duplex: 'half',
        credentials: isCredentialsSupported ? withCredentials : undefined,
      });

      if (isRequestSupported) {
        utils$1.forEach(requestDefaults, (value, key) => {
          if (resolvedOptions[key] === undefined) {
            resolvedOptions[key] = value;
          }
        });

        if (resolvedOptions.signal === undefined) {
          resolvedOptions.signal = null;
        }

        if (resolvedOptions.body === undefined) {
          resolvedOptions.body = null;
        }
      }

      if (maxRedirects === 0) {
        resolvedOptions.redirect = 'manual';

        if (safeFetchOptions) {
          safeFetchOptions.redirect = 'manual';
        }
      }

      request = isRequestSupported && new Request(url, resolvedOptions);

      let response = await (isRequestSupported
        ? _fetch(request, safeFetchOptions)
        : _fetch(url, resolvedOptions));

      const responseHeaders = AxiosHeaders$1.from(response.headers);

      // Cheap pre-check: if the server honestly declares a content-length that
      // already exceeds the cap, reject before we start streaming.
      if (hasMaxContentLength) {
        const declaredLength = utils$1.toFiniteNumber(responseHeaders.getContentLength());
        if (declaredLength != null && declaredLength > maxContentLength) {
          throw new AxiosError$1(
            'maxContentLength size of ' + maxContentLength + ' exceeded',
            AxiosError$1.ERR_BAD_RESPONSE,
            config,
            request
          );
        }
      }

      const isStreamResponse =
        supportsResponseStream && (responseType === 'stream' || responseType === 'response');

      if (
        supportsResponseStream &&
        response.body &&
        (onDownloadProgress || hasMaxContentLength || (isStreamResponse && unsubscribe))
      ) {
        const options = {};

        ['status', 'statusText', 'headers'].forEach((prop) => {
          options[prop] = response[prop];
        });

        const responseContentLength = utils$1.toFiniteNumber(responseHeaders.getContentLength());

        const [onProgress, flush] =
          (onDownloadProgress &&
            progressEventDecorator(
              responseContentLength,
              progressEventReducer(asyncDecorator(onDownloadProgress), true)
            )) ||
          [];

        let bytesRead = 0;
        const onChunkProgress = (loadedBytes) => {
          if (hasMaxContentLength) {
            bytesRead = loadedBytes;
            if (bytesRead > maxContentLength) {
              throw (pendingResponseError = new AxiosError$1(
                'maxContentLength size of ' + maxContentLength + ' exceeded',
                AxiosError$1.ERR_BAD_RESPONSE,
                config,
                request
              ));
            }
          }
          onProgress && onProgress(loadedBytes);
        };

        response = new Response(
          trackStream(response.body, DEFAULT_CHUNK_SIZE, onChunkProgress, () => {
            flush && flush();
            unsubscribe && unsubscribe();
          }),
          options
        );
      }

      responseType = responseType || 'text';

      let responseData = await resolvers[utils$1.findKey(resolvers, responseType) || 'text'](
        response,
        config
      );

      // Fallback enforcement for environments without ReadableStream support
      // (legacy runtimes). Detect materialized size from typed output; skip
      // streams/Response passthrough since the user will read those themselves.
      if (hasMaxContentLength && !supportsResponseStream && !isStreamResponse) {
        let materializedSize;
        if (responseData != null) {
          if (typeof responseData.byteLength === 'number') {
            materializedSize = responseData.byteLength;
          } else if (typeof responseData.size === 'number') {
            materializedSize = responseData.size;
          } else if (typeof responseData === 'string') {
            materializedSize =
              typeof TextEncoder === 'function'
                ? new TextEncoder().encode(responseData).byteLength
                : responseData.length;
          }
        }
        if (typeof materializedSize === 'number' && materializedSize > maxContentLength) {
          throw new AxiosError$1(
            'maxContentLength size of ' + maxContentLength + ' exceeded',
            AxiosError$1.ERR_BAD_RESPONSE,
            config,
            request
          );
        }
      }

      !isStreamResponse && unsubscribe && unsubscribe();

      return await new Promise((resolve, reject) => {
        settle(resolve, reject, {
          data: responseData,
          headers: AxiosHeaders$1.from(response.headers),
          status: response.status,
          statusText: response.statusText,
          config,
          request,
        });
      });
    } catch (err) {
      unsubscribe && unsubscribe();

      // Safari can surface fetch aborts as a DOMException-like object whose
      // branded getters throw. Prefer our composed signal reason before reading
      // the caught error, preserving timeout vs cancellation semantics.
      if (composedSignal && composedSignal.aborted && composedSignal.reason instanceof AxiosError$1) {
        const canceledError = composedSignal.reason;
        canceledError.config = config;
        request && (canceledError.request = request);
        if (err !== canceledError) {
          // Non-enumerable to match native Error `cause` semantics so loggers
          // don't recurse into circular fetch internals (see #7205).
          Object.defineProperty(canceledError, 'cause', {
            __proto__: null,
            value: err,
            writable: true,
            enumerable: false,
            configurable: true,
          });
        }
        throw canceledError;
      }

      // Surface a maxBodyLength violation we raised while the request body was
      // being streamed. Keeping the original error (rather than reading
      // `err.cause.isAxiosError`) keeps the error deterministic across runtimes
      // and avoids both prototype-pollution reads and mis-attributing a foreign
      // AxiosError that merely happened to land in `err.cause`.
      if (pendingBodyError) {
        request && !pendingBodyError.request && (pendingBodyError.request = request);
        throw pendingBodyError;
      }

      if (pendingResponseError) {
        throw pendingResponseError;
      }

      // Re-throw AxiosErrors we raised synchronously (data: URL / content-length
      // pre-checks, response size enforcement) without re-wrapping them.
      if (err instanceof AxiosError$1) {
        request && !err.request && (err.request = request);
        throw err;
      }

      if (err && err.name === 'TypeError' && /Load failed|fetch/i.test(err.message)) {
        const networkError = new AxiosError$1(
          'Network Error',
          AxiosError$1.ERR_NETWORK,
          config,
          request,
          err && err.response
        );
        // Non-enumerable to match native Error `cause` semantics so loggers
        // don't recurse into circular fetch internals (see #7205).
        Object.defineProperty(networkError, 'cause', {
          __proto__: null,
          value: err.cause || err,
          writable: true,
          enumerable: false,
          configurable: true,
        });
        throw networkError;
      }

      throw AxiosError$1.from(err, err && err.code, config, request, err && err.response);
    }
  };
};

const seedCache = new Map();

const getFetch = (config) => {
  const env = Object.create(null);
  const configuredEnv = config && utils$1.hasOwnProp(config, 'env') && config.env;
  ['fetch', 'Request', 'Response', 'Blob'].forEach((key) => {
    if (configuredEnv && utils$1.hasOwnProp(configuredEnv, key)) {
      env[key] = configuredEnv[key];
    }
  });
  const { fetch, Request, Response, Blob } = env;
  const seeds = [Request, Response, fetch, Blob];

  let len = seeds.length,
    i = len,
    seed,
    target,
    map = seedCache;

  while (i--) {
    seed = seeds[i];
    target = map.get(seed);

    target === undefined && map.set(seed, (target = i ? new Map() : factory(env)));

    map = target;
  }

  return target;
};

getFetch();

/**
 * Known adapters mapping.
 * Provides environment-specific adapters for Axios:
 * - `http` for Node.js
 * - `xhr` for browsers
 * - `fetch` for fetch API-based requests
 *
 * @type {Object<string, Function|Object>}
 */
const knownAdapters = {
  http: httpAdapter,
  xhr: xhrAdapter,
  fetch: {
    get: getFetch,
  },
};

// Assign adapter names for easier debugging and identification
utils$1.forEach(knownAdapters, (fn, value) => {
  if (fn) {
    try {
      // Null-proto descriptors so a polluted Object.prototype.get cannot turn
      // these data descriptors into accessor descriptors on the way in.
      Object.defineProperty(fn, 'name', { __proto__: null, value });
    } catch (e) {
      // eslint-disable-next-line no-empty
    }
    Object.defineProperty(fn, 'adapterName', { __proto__: null, value });
  }
});

/**
 * Render a rejection reason string for unknown or unsupported adapters
 *
 * @param {string} reason
 * @returns {string}
 */
const renderReason = (reason) => `- ${reason}`;

/**
 * Check if the adapter is resolved (function, null, or false)
 *
 * @param {Function|null|false} adapter
 * @returns {boolean}
 */
const isResolvedHandle = (adapter) =>
  utils$1.isFunction(adapter) || adapter === null || adapter === false;

/**
 * Get the first suitable adapter from the provided list.
 * Tries each adapter in order until a supported one is found.
 * Throws an AxiosError if no adapter is suitable.
 *
 * @param {Array<string|Function>|string|Function} adapters - Adapter(s) by name or function.
 * @param {Object} config - Axios request configuration
 * @throws {AxiosError} If no suitable adapter is available
 * @returns {Function} The resolved adapter function
 */
function getAdapter(adapters, config) {
  adapters = utils$1.isArray(adapters) ? adapters : [adapters];

  const { length } = adapters;
  let nameOrAdapter;
  let adapter;

  const rejectedReasons = {};

  for (let i = 0; i < length; i++) {
    nameOrAdapter = adapters[i];
    let id;

    adapter = nameOrAdapter;

    if (!isResolvedHandle(nameOrAdapter)) {
      adapter = knownAdapters[(id = String(nameOrAdapter)).toLowerCase()];

      if (adapter === undefined) {
        throw new AxiosError$1(`Unknown adapter '${id}'`);
      }
    }

    if (adapter && (utils$1.isFunction(adapter) || (adapter = adapter.get(config)))) {
      break;
    }

    rejectedReasons[id || '#' + i] = adapter;
  }

  if (!adapter) {
    const reasons = Object.entries(rejectedReasons).map(
      ([id, state]) =>
        `adapter ${id} ` +
        (state === false ? 'is not supported by the environment' : 'is not available in the build')
    );

    let s = length
      ? reasons.length > 1
        ? 'since :\n' + reasons.map(renderReason).join('\n')
        : ' ' + renderReason(reasons[0])
      : 'as no adapter specified';

    throw new AxiosError$1(
      `There is no suitable adapter to dispatch the request ` + s,
      AxiosError$1.ERR_NOT_SUPPORT
    );
  }

  return adapter;
}

/**
 * Exports Axios adapters and utility to resolve an adapter
 */
const adapters = {
  /**
   * Resolve an adapter from a list of adapter names or functions.
   * @type {Function}
   */
  getAdapter,

  /**
   * Exposes all known adapters
   * @type {Object<string, Function|Object>}
   */
  adapters: knownAdapters,
};

/**
 * Throws a `CanceledError` if cancellation has been requested.
 *
 * @param {Object} config The config that is to be used for the request
 *
 * @returns {void}
 */
function throwIfCancellationRequested(config) {
  if (config.cancelToken) {
    config.cancelToken.throwIfRequested();
  }

  if (config.signal && config.signal.aborted) {
    throw new CanceledError$1(null, config);
  }
}

/**
 * Milliseconds elapsed since `start`, floored at zero.
 *
 * Wall-clock, to match the rest of the codebase (speedometer, throttle,
 * AxiosTransformStream). A backwards clock adjustment mid-request would
 * otherwise produce a negative duration, so the result is clamped.
 *
 * @param {number} start Timestamp from `Date.now()`
 *
 * @returns {number} Non-negative elapsed milliseconds
 */
function elapsedSince(start) {
  return Math.max(0, Date.now() - start);
}

/**
 * Dispatch a request to the server using the configured adapter.
 *
 * @param {object} config The config that is to be used for the request
 *
 * @returns {Promise} The Promise to be fulfilled
 */
function dispatchRequest(_config) {
  // Interceptors may replace the merged config with an ordinary object. Flatten
  // it at the dispatch boundary so shared prototype members cannot become
  // request behavior, while preserving intentional template/class members.
  const config = utils$1.toSafeFlatObject(_config);

  throwIfCancellationRequested(config);

  config.headers = AxiosHeaders$1.from(utils$1.getSafeProp(config, 'headers'));

  // Transform request data
  config.data = transformData.call(config, config.transformRequest);

  if (['post', 'put', 'patch'].indexOf(config.method) !== -1) {
    config.headers.setContentType('application/x-www-form-urlencoded', false);
  }

  const adapter = adapters.getAdapter(config.adapter || defaults$1.adapter, config);

  const start = Date.now();

  return adapter(config).then(
    function onAdapterResolution(response) {
      throwIfCancellationRequested(config);

      response.duration = elapsedSince(start);

      // Expose the current response on config so that transformResponse can
      // attach it to any AxiosError it throws (e.g. on JSON parse failure).
      // We clean it up afterwards to avoid polluting the config object.
      config.response = response;
      try {
        response.data = transformData.call(config, config.transformResponse, response);
      } finally {
        delete config.response;
      }

      response.headers = AxiosHeaders$1.from(response.headers);

      return response;
    },
    function onAdapterRejection(reason) {
      if (!isCancel(reason)) {
        throwIfCancellationRequested(config);

        // Transform response data
        if (reason && reason.response) {
          reason.response.duration = elapsedSince(start);
          config.response = reason.response;
          try {
            reason.response.data = transformData.call(
              config,
              config.transformResponse,
              reason.response
            );
          } finally {
            delete config.response;
          }
          reason.response.headers = AxiosHeaders$1.from(reason.response.headers);
        }
      }

      return Promise.reject(reason);
    }
  );
}

const validators$1 = {};

// eslint-disable-next-line func-names
['object', 'boolean', 'number', 'function', 'string', 'symbol'].forEach((type, i) => {
  validators$1[type] = function validator(thing) {
    return typeof thing === type || 'a' + (i < 1 ? 'n ' : ' ') + type;
  };
});

const deprecatedWarnings = {};

/**
 * Transitional option validator
 *
 * @param {function|boolean?} validator - set to false if the transitional option has been removed
 * @param {string?} version - deprecated version / removed since version
 * @param {string?} message - some message with additional info
 *
 * @returns {function}
 */
validators$1.transitional = function transitional(validator, version, message) {
  function formatMessage(opt, desc) {
    return (
      '[Axios v' +
      VERSION +
      "] Transitional option '" +
      opt +
      "'" +
      desc +
      (message ? '. ' + message : '')
    );
  }

  // eslint-disable-next-line func-names
  return (value, opt, opts) => {
    if (validator === false) {
      throw new AxiosError$1(
        formatMessage(opt, ' has been removed' + (version ? ' in ' + version : '')),
        AxiosError$1.ERR_DEPRECATED
      );
    }

    if (version && !deprecatedWarnings[opt]) {
      deprecatedWarnings[opt] = true;
      // eslint-disable-next-line no-console
      console.warn(
        formatMessage(
          opt,
          ' has been deprecated since v' + version + ' and will be removed in the near future'
        )
      );
    }

    return validator ? validator(value, opt, opts) : true;
  };
};

validators$1.spelling = function spelling(correctSpelling) {
  return (value, opt) => {
    // eslint-disable-next-line no-console
    console.warn(`${opt} is likely a misspelling of ${correctSpelling}`);
    return true;
  };
};

/**
 * Assert object's properties type
 *
 * @param {object} options
 * @param {object} schema
 * @param {boolean?} allowUnknown
 *
 * @returns {object}
 */

function assertOptions(options, schema, allowUnknown) {
  if (typeof options !== 'object' || options === null) {
    throw new AxiosError$1('options must be an object', AxiosError$1.ERR_BAD_OPTION_VALUE);
  }
  const keys = Object.keys(options);
  let i = keys.length;
  while (i-- > 0) {
    const opt = keys[i];
    // Use hasOwnProperty so a polluted Object.prototype.<opt> cannot supply
    // a non-function validator and cause a TypeError.
    const validator = Object.prototype.hasOwnProperty.call(schema, opt) ? schema[opt] : undefined;
    if (validator) {
      const value = options[opt];
      const result = value === undefined || validator(value, opt, options);
      if (result !== true) {
        throw new AxiosError$1(
          'option ' + opt + ' must be ' + result,
          AxiosError$1.ERR_BAD_OPTION_VALUE
        );
      }
      continue;
    }
    if (allowUnknown !== true) {
      throw new AxiosError$1('Unknown option ' + opt, AxiosError$1.ERR_BAD_OPTION);
    }
  }
}

const validator = {
  assertOptions,
  validators: validators$1,
};

const validators = validator.validators;

// Recognize header maps without consuming objects intended as literal values.
// AxiosHeaders from other builds share a brand and header-container interface,
// but not constructor identity. A tag and toJSON alone can describe a literal.
const isHeadersBucket = (value) => {
  if (value == null || utils$1.isPlainObject(value) || value instanceof AxiosHeaders$1) {
    return true;
  }

  try {
    return (
      utils$1.isObject(value) &&
      utils$1.getSafeProp(value, Symbol.toStringTag) === 'AxiosHeaders' &&
      [
        'toJSON',
        'set',
        'get',
        'has',
        'delete',
        'clear',
        'normalize',
        'concat',
        'toString',
        Symbol.iterator,
      ].every((method) => utils$1.isFunction(utils$1.getSafeProp(value, method)))
    );
  } catch (e) {
    // A failed optional brand probe must not prevent literal header serialization.
    return false;
  }
};

/**
 * Create a new instance of Axios
 *
 * @param {Object} instanceConfig The default config for the instance
 *
 * @return {Axios} A new instance of Axios
 */
class Axios {
  constructor(instanceConfig) {
    this.defaults = instanceConfig || {};
    this.interceptors = {
      request: new InterceptorManager$1(),
      response: new InterceptorManager$1(),
    };
  }

  /**
   * Dispatch a request
   *
   * @param {String|Object} configOrUrl The config specific for this request (merged with this.defaults)
   * @param {?Object} config
   *
   * @returns {Promise} The Promise to be fulfilled
   */
  async request(configOrUrl, config) {
    try {
      return await this._request(configOrUrl, config);
    } catch (err) {
      if (err instanceof Error) {
        try {
          let dummy = {};

          Error.captureStackTrace ? Error.captureStackTrace(dummy) : (dummy = new Error());

          const dummyStack = dummy.stack;
          let stack = '';

          // slice off the Error: ... line
          if (typeof dummyStack === 'string') {
            const firstNewlineIndex = dummyStack.indexOf('\n');

            stack = firstNewlineIndex === -1 ? '' : dummyStack.slice(firstNewlineIndex + 1);
          }

          if (!err.stack) {
            err.stack = stack;
          } else if (stack) {
            // Match a common suffix after the 2 top frames when available,
            // otherwise compare the full reconstructed stack.
            const firstNewlineIndex = stack.indexOf('\n');
            const secondNewlineIndex =
              firstNewlineIndex === -1 ? -1 : stack.indexOf('\n', firstNewlineIndex + 1);
            const duplicateCheckSuffix =
              secondNewlineIndex === -1 ? stack : stack.slice(secondNewlineIndex + 1);

            // `AxiosError.from()` may have already inlined the wrapped error's
            // stack under a `Caused by:` marker. Keep the reconstructed caller
            // frames ahead of that marker so stack-only reporters do not read
            // them as part of the low-level cause.
            const currentStack = String(err.stack);
            const causeIndex = getCauseStackIndex(err, currentStack);
            const stackHead = causeIndex === -1 ? currentStack : currentStack.slice(0, causeIndex);
            const causeSection = causeIndex === -1 ? '' : currentStack.slice(causeIndex);

            if (!stackHead.endsWith(duplicateCheckSuffix)) {
              err.stack = stackHead + '\n' + stack + causeSection;
            }
          }
        } catch (e) {
          // Ignore failures from custom stack hooks or un-writable stack properties.
        }
      }

      throw err;
    }
  }

  _request(configOrUrl, config) {
    /*eslint no-param-reassign:0*/
    // Allow for axios('example/url'[, config]) a la fetch API
    if (typeof configOrUrl === 'string') {
      config = config || {};
      config.url = configOrUrl;
    } else {
      config = configOrUrl || {};
    }

    config = mergeConfig(this.defaults, config);

    const { transitional, paramsSerializer, headers } = config;

    if (transitional !== undefined) {
      validator.assertOptions(
        transitional,
        {
          silentJSONParsing: validators.transitional(validators.boolean),
          forcedJSONParsing: validators.transitional(validators.boolean),
          clarifyTimeoutError: validators.transitional(validators.boolean),
          legacyInterceptorReqResOrdering: validators.transitional(validators.boolean),
          advertiseZstdAcceptEncoding: validators.transitional(validators.boolean),
          validateStatusUndefinedResolves: validators.transitional(validators.boolean),
          encodeBasicAuthUsername: validators.transitional(validators.boolean),
        },
        false
      );
    }

    if (paramsSerializer != null) {
      if (utils$1.isFunction(paramsSerializer)) {
        config.paramsSerializer = {
          serialize: paramsSerializer,
        };
      } else {
        validator.assertOptions(
          paramsSerializer,
          {
            encode: validators.function,
            serialize: validators.function,
          },
          true
        );
      }
    }

    // Set config.allowAbsoluteUrls
    if (config.allowAbsoluteUrls !== undefined) ; else if (
      utils$1.hasOwnProp(this.defaults, 'allowAbsoluteUrls') &&
      this.defaults.allowAbsoluteUrls !== undefined
    ) {
      config.allowAbsoluteUrls = this.defaults.allowAbsoluteUrls;
    } else {
      config.allowAbsoluteUrls = true;
    }

    validator.assertOptions(
      config,
      {
        baseUrl: validators.spelling('baseURL'),
        withXsrfToken: validators.spelling('withXSRFToken'),
      },
      true
    );

    // Set config.method
    config.method = (
      utils$1.getSafeProp(config, 'method') ||
      utils$1.getSafeProp(this.defaults, 'method') ||
      'get'
    ).toLowerCase();

    // Flatten header defaults without consuming literal method-named headers.
    const commonHeaders = utils$1.getSafeProp(headers, 'common');
    const methodHeaders = utils$1.getSafeProp(headers, config.method);
    const contextHeaders =
      headers &&
      utils$1.merge(
        isHeadersBucket(commonHeaders) ? commonHeaders : undefined,
        isHeadersBucket(methodHeaders) ? methodHeaders : undefined
      );

    headers &&
      utils$1.forEach(methodList$1.concat('common'), (method) => {
        if (isHeadersBucket(utils$1.getSafeProp(headers, method))) {
          delete headers[method];
        }
      });

    config.headers = AxiosHeaders$1.concat(contextHeaders, headers);

    // filter out skipped interceptors
    const requestInterceptorChain = [];
    let synchronousRequestInterceptors = true;
    this.interceptors.request.forEach(function unshiftRequestInterceptors(interceptor) {
      if (typeof interceptor.runWhen === 'function' && interceptor.runWhen(config) === false) {
        return;
      }

      synchronousRequestInterceptors = synchronousRequestInterceptors && interceptor.synchronous;

      const transitional = config.transitional || transitionalDefaults;
      const legacyInterceptorReqResOrdering =
        transitional && transitional.legacyInterceptorReqResOrdering;

      if (legacyInterceptorReqResOrdering) {
        requestInterceptorChain.unshift(interceptor.fulfilled, interceptor.rejected);
      } else {
        requestInterceptorChain.push(interceptor.fulfilled, interceptor.rejected);
      }
    });

    const responseInterceptorChain = [];
    this.interceptors.response.forEach(function pushResponseInterceptors(interceptor) {
      responseInterceptorChain.push(interceptor.fulfilled, interceptor.rejected);
    });

    let promise;
    let i = 0;
    let len;

    if (!synchronousRequestInterceptors) {
      const chain = [dispatchRequest.bind(this), undefined];
      chain.unshift(...requestInterceptorChain);
      chain.push(...responseInterceptorChain);
      len = chain.length;

      promise = Promise.resolve(config);

      while (i < len) {
        promise = promise.then(chain[i++], chain[i++]);
      }

      return promise;
    }

    len = requestInterceptorChain.length;

    let newConfig = config;

    while (i < len) {
      const onFulfilled = requestInterceptorChain[i++];
      const onRejected = requestInterceptorChain[i++];
      try {
        newConfig = onFulfilled ? onFulfilled(newConfig) : newConfig;
      } catch (error) {
        if (!onRejected) {
          promise = Promise.reject(error);
          break;
        }

        try {
          const rejectedResult = onRejected.call(this, error);

          if (utils$1.isThenable(rejectedResult)) {
            promise = Promise.resolve(rejectedResult).then(() =>
              dispatchRequest.call(this, newConfig)
            );
          }
        } catch (rejectedError) {
          promise = Promise.reject(rejectedError);
        }

        break;
      }
    }

    if (!promise) {
      try {
        promise = dispatchRequest.call(this, newConfig);
      } catch (error) {
        promise = Promise.reject(error);
      }
    }

    i = 0;
    len = responseInterceptorChain.length;

    while (i < len) {
      promise = promise.then(responseInterceptorChain[i++], responseInterceptorChain[i++]);
    }

    return promise;
  }

  getUri(config) {
    config = mergeConfig(this.defaults, config);
    const fullPath = buildFullPath(config.baseURL, config.url, config.allowAbsoluteUrls, config);
    return buildURL(fullPath, config.params, config.paramsSerializer);
  }
}

// Provide aliases for supported request methods
utils$1.forEach(['delete', 'get', 'head', 'options'], function forEachMethodNoData(method) {
  /*eslint func-names:0*/
  Axios.prototype[method] = async function (url, config) {
    return this.request(
      mergeConfig(config || {}, {
        method,
        url,
        data: config && utils$1.hasOwnProp(config, 'data') ? config.data : undefined,
      })
    );
  };
});

utils$1.forEach(['post', 'put', 'patch', 'query'], function forEachMethodWithData(method) {
  function generateHTTPMethod(isForm) {
    return async function httpMethod(url, data, config) {
      return this.request(
        mergeConfig(config || {}, {
          method,
          headers: isForm
            ? {
                'Content-Type': 'multipart/form-data',
              }
            : {},
          url,
          data,
        })
      );
    };
  }

  Axios.prototype[method] = generateHTTPMethod();

  // QUERY is a safe/idempotent read method; multipart form bodies don't fit
  // its semantics, so no queryForm shorthand is generated.
  if (method !== 'query') {
    Axios.prototype[method + 'Form'] = generateHTTPMethod(true);
  }
});

const Axios$1 = Axios;

/**
 * A `CancelToken` is an object that can be used to request cancellation of an operation.
 *
 * @param {Function} executor The executor function.
 *
 * @returns {CancelToken}
 */
class CancelToken {
  constructor(executor) {
    if (typeof executor !== 'function') {
      throw new TypeError('executor must be a function.');
    }

    let resolvePromise;

    this.promise = new Promise(function promiseExecutor(resolve) {
      resolvePromise = resolve;
    });

    const token = this;

    // eslint-disable-next-line func-names
    this.promise.then((cancel) => {
      if (!token._listeners) return;

      let i = token._listeners.length;

      while (i-- > 0) {
        token._listeners[i](cancel);
      }
      token._listeners = null;
    });

    // eslint-disable-next-line func-names
    this.promise.then = (onfulfilled) => {
      let _resolve;
      // eslint-disable-next-line func-names
      const promise = new Promise((resolve) => {
        token.subscribe(resolve);
        _resolve = resolve;
      }).then(onfulfilled);

      promise.cancel = function reject() {
        token.unsubscribe(_resolve);
      };

      return promise;
    };

    executor(function cancel(message, config, request) {
      if (token.reason) {
        // Cancellation has already been requested
        return;
      }

      token.reason = new CanceledError$1(message, config, request);
      resolvePromise(token.reason);
    });
  }

  /**
   * Throws a `CanceledError` if cancellation has been requested.
   */
  throwIfRequested() {
    if (this.reason) {
      throw this.reason;
    }
  }

  /**
   * Subscribe to the cancel signal
   */

  subscribe(listener) {
    if (this.reason) {
      listener(this.reason);
      return;
    }

    if (this._listeners) {
      this._listeners.push(listener);
    } else {
      this._listeners = [listener];
    }
  }

  /**
   * Unsubscribe from the cancel signal
   */

  unsubscribe(listener) {
    if (!this._listeners) {
      return;
    }
    const index = this._listeners.indexOf(listener);
    if (index !== -1) {
      this._listeners.splice(index, 1);
    }
  }

  toAbortSignal() {
    const controller = new AbortController();

    const abort = (err) => {
      controller.abort(err);
    };

    this.subscribe(abort);

    controller.signal.unsubscribe = () => this.unsubscribe(abort);

    return controller.signal;
  }

  /**
   * Returns an object that contains a new `CancelToken` and a function that, when called,
   * cancels the `CancelToken`.
   */
  static source() {
    let cancel;
    const token = new CancelToken(function executor(c) {
      cancel = c;
    });
    return {
      token,
      cancel,
    };
  }
}

const CancelToken$1 = CancelToken;

/**
 * Syntactic sugar for invoking a function and expanding an array for arguments.
 *
 * Common use case would be to use `Function.prototype.apply`.
 *
 *  ```js
 *  function f(x, y, z) {}
 *  const args = [1, 2, 3];
 *  f.apply(null, args);
 *  ```
 *
 * With `spread` this example can be re-written.
 *
 *  ```js
 *  spread(function(x, y, z) {})([1, 2, 3]);
 *  ```
 *
 * @param {Function} callback
 *
 * @returns {Function}
 */
function spread(callback) {
  return function wrap(arr) {
    return callback.apply(null, arr);
  };
}

/**
 * Determines whether the payload is an error thrown by Axios
 *
 * @param {*} payload The value to test
 *
 * @returns {boolean} True if the payload is an error thrown by Axios, otherwise false
 */
function isAxiosError(payload) {
  return utils$1.isObject(payload) && payload.isAxiosError === true;
}

const HttpStatusCode = {
  Continue: 100,
  SwitchingProtocols: 101,
  Processing: 102,
  EarlyHints: 103,
  Ok: 200,
  Created: 201,
  Accepted: 202,
  NonAuthoritativeInformation: 203,
  NoContent: 204,
  ResetContent: 205,
  PartialContent: 206,
  MultiStatus: 207,
  AlreadyReported: 208,
  ImUsed: 226,
  MultipleChoices: 300,
  MovedPermanently: 301,
  Found: 302,
  SeeOther: 303,
  NotModified: 304,
  UseProxy: 305,
  Unused: 306,
  TemporaryRedirect: 307,
  PermanentRedirect: 308,
  BadRequest: 400,
  Unauthorized: 401,
  PaymentRequired: 402,
  Forbidden: 403,
  NotFound: 404,
  MethodNotAllowed: 405,
  NotAcceptable: 406,
  ProxyAuthenticationRequired: 407,
  RequestTimeout: 408,
  Conflict: 409,
  Gone: 410,
  LengthRequired: 411,
  PreconditionFailed: 412,
  /**
   * @deprecated Use `ContentTooLarge` instead.
   */
  PayloadTooLarge: 413,
  ContentTooLarge: 413,
  UriTooLong: 414,
  UnsupportedMediaType: 415,
  RangeNotSatisfiable: 416,
  ExpectationFailed: 417,
  ImATeapot: 418,
  MisdirectedRequest: 421,
  /**
   * @deprecated Use `UnprocessableContent` instead.
   */
  UnprocessableEntity: 422,
  UnprocessableContent: 422,
  Locked: 423,
  FailedDependency: 424,
  TooEarly: 425,
  UpgradeRequired: 426,
  PreconditionRequired: 428,
  TooManyRequests: 429,
  RequestHeaderFieldsTooLarge: 431,
  UnavailableForLegalReasons: 451,
  InternalServerError: 500,
  NotImplemented: 501,
  BadGateway: 502,
  ServiceUnavailable: 503,
  GatewayTimeout: 504,
  HttpVersionNotSupported: 505,
  VariantAlsoNegotiates: 506,
  InsufficientStorage: 507,
  LoopDetected: 508,
  NotExtended: 510,
  NetworkAuthenticationRequired: 511,
  WebServerReturnsAnUnknownError: 520,
  WebServerIsDown: 521,
  ConnectionTimedOut: 522,
  OriginIsUnreachable: 523,
  TimeoutOccurred: 524,
  SslHandshakeFailed: 525,
  InvalidSslCertificate: 526,
};

Object.entries(HttpStatusCode).forEach(([key, value]) => {
  if (HttpStatusCode[value] === undefined) {
    HttpStatusCode[value] = key;
  }
});

const HttpStatusCode$1 = HttpStatusCode;

/**
 * Create an instance of Axios
 *
 * @param {Object} defaultConfig The default config for the instance
 *
 * @returns {Axios} A new instance of Axios
 */
function createInstance(defaultConfig) {
  const context = new Axios$1(defaultConfig);
  const instance = bind(Axios$1.prototype.request, context);

  // Copy axios.prototype to instance
  utils$1.extend(instance, Axios$1.prototype, context, { allOwnKeys: true });

  // Copy context to instance
  utils$1.extend(instance, context, null, { allOwnKeys: true });

  // Factory for creating new instances
  instance.create = function create(instanceConfig) {
    return createInstance(mergeConfig(defaultConfig, instanceConfig));
  };

  return instance;
}

// Create the default instance to be exported
const axios = createInstance(defaults$1);

// Expose Axios class to allow class inheritance
axios.Axios = Axios$1;

// Expose Cancel & CancelToken
axios.CanceledError = CanceledError$1;
axios.CancelToken = CancelToken$1;
axios.isCancel = isCancel;
axios.VERSION = VERSION;
axios.toFormData = toFormData;

// Expose AxiosError class
axios.AxiosError = AxiosError$1;

// alias for CanceledError for backward compatibility
axios.Cancel = axios.CanceledError;

// Expose all/spread
axios.all = function all(promises) {
  return Promise.all(promises);
};

axios.spread = spread;

// Expose isAxiosError
axios.isAxiosError = isAxiosError;

// Expose mergeConfig
axios.mergeConfig = mergeConfig;

axios.AxiosHeaders = AxiosHeaders$1;

axios.formToJSON = (thing) => formDataToJSON(utils$1.isHTMLForm(thing) ? new FormData(thing) : thing);

axios.getAdapter = adapters.getAdapter;

axios.HttpStatusCode = HttpStatusCode$1;

axios.default = axios;

// this module should only have a default export
const axios$1 = axios;

const AppPage_vue_vue_type_style_index_0_scoped_ecb8b42c_lang = '';

const {createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,createElementVNode:_createElementVNode,toDisplayString:_toDisplayString,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,mergeProps:_mergeProps,withModifiers:_withModifiers,Fragment:_Fragment,createElementBlock:_createElementBlock,renderList:_renderList,normalizeClass:_normalizeClass,normalizeStyle:_normalizeStyle,withKeys:_withKeys} = await importShared('vue');


const _hoisted_1 = { class: "app-page" };
const _hoisted_2 = { class: "page-header d-flex align-center flex-wrap ga-3 mb-4" };
const _hoisted_3 = { class: "text-caption text-medium-emphasis mb-2" };
const _hoisted_4 = { class: "d-flex justify-space-between text-body-2 mt-1" };
const _hoisted_5 = { class: "text-medium-emphasis" };
const _hoisted_6 = { class: "d-flex justify-space-between text-body-2 mt-1" };
const _hoisted_7 = { class: "text-medium-emphasis" };
const _hoisted_8 = { class: "d-flex align-center flex-wrap ga-2" };
const _hoisted_9 = { class: "text-body-2" };
const _hoisted_10 = { class: "text-caption text-medium-emphasis" };
const _hoisted_11 = {
  key: 1,
  class: "chart-grid"
};
const _hoisted_12 = { class: "d-flex justify-space-between text-caption mb-1" };
const _hoisted_13 = {
  class: "mini-chart",
  viewBox: "0 0 300 64",
  preserveAspectRatio: "none"
};
const _hoisted_14 = ["points", "fill"];
const _hoisted_15 = ["points", "stroke"];
const _hoisted_16 = {
  key: 2,
  class: "text-caption text-medium-emphasis text-center py-4"
};
const _hoisted_17 = { class: "d-flex align-center flex-wrap ga-2" };
const _hoisted_18 = { class: "font-weight-medium" };
const _hoisted_19 = { class: "text-caption text-medium-emphasis" };
const _hoisted_20 = {
  key: 0,
  class: "text-caption text-medium-emphasis"
};
const _hoisted_21 = { class: "d-flex ga-1" };
const _hoisted_22 = { class: "d-flex align-center flex-wrap ga-2" };
const _hoisted_23 = ["title"];
const _hoisted_24 = { class: "text-caption text-medium-emphasis" };
const _hoisted_25 = { class: "d-flex ga-1" };
const _hoisted_26 = { class: "d-flex align-center flex-wrap ga-2" };
const _hoisted_27 = ["title"];
const _hoisted_28 = { class: "text-caption text-medium-emphasis" };
const _hoisted_29 = { class: "text-subtitle-1" };
const _hoisted_30 = { class: "screen-wrap" };
const _hoisted_31 = {
  key: 0,
  class: "text-caption text-error pa-4 text-center"
};
const _hoisted_32 = ["src"];
const _hoisted_33 = { class: "text-subtitle-1" };
const _hoisted_34 = {
  key: 0,
  class: "text-grey text-caption pa-3"
};
const _hoisted_35 = {
  key: 1,
  class: "terminal-pre"
};
const _hoisted_36 = {
  key: 2,
  class: "text-caption text-warning pa-2"
};
const _hoisted_37 = { class: "pa-2 d-flex flex-wrap ga-1 quick-cmds" };
const _hoisted_38 = { class: "d-flex align-center ga-2" };
const _hoisted_39 = { class: "text-caption text-medium-emphasis" };
const _hoisted_40 = {
  key: 0,
  class: "chart-grid"
};
const _hoisted_41 = { class: "d-flex justify-space-between text-caption mb-1" };
const _hoisted_42 = {
  class: "mini-chart",
  viewBox: "0 0 300 64",
  preserveAspectRatio: "none"
};
const _hoisted_43 = ["points", "fill"];
const _hoisted_44 = ["points", "stroke"];
const _hoisted_45 = {
  key: 1,
  class: "text-caption text-medium-emphasis text-center py-6"
};
const _hoisted_46 = ["title"];
const _hoisted_47 = { class: "text-caption text-medium-emphasis" };

const {computed,nextTick,onBeforeUnmount,onMounted,reactive,ref,watch} = await importShared('vue');

const CACHE_PREFIX = 'pveCache_';
const CACHE_TTL = 2 * 3600 * 1000;


const _sfc_main = {
  __name: 'AppPage',
  props: {
  api: { type: [Object, Function], required: true },
  pluginId: { type: String, default: 'ProxmoxVEBackup' },
},
  setup(__props) {

const props = __props;

const pluginId = computed(() => props.pluginId || 'ProxmoxVEBackup');
const API_BASE = computed(() => `plugin/${pluginId.value}`);

// ---------- 状态 ----------
const refreshing = ref(false);
const refreshInterval = ref(30);
const refreshOptions = [
  { title: '10 秒', value: 10 },
  { title: '30 秒', value: 30 },
  { title: '60 秒', value: 60 },
  { title: '手动', value: 0 },
];
const collapsed = reactive({ host: false, vm: false, files: false, mon: false, tasks: false });

const pve = ref({});
const status = ref({});
const vmList = ref([]);
const backupFiles = ref([]);

// ---------- PVE 监控（RRD） ----------
const monitorData = ref(null);
const monitorLoading = ref(false);
const monitorTf = ref('hour');
const guestDialog = reactive({ show: false, vmid: null, type: 'qemu', name: '' });
const guestTf = ref('hour');
const guestData = ref(null);
const guestLoading = ref(false);

const vmSearch = ref('');
const fileSearch = ref('');
const fileSource = ref('全部');

// ---------- 宿主机终端 ----------
const termDialog = ref(false);
const termOutput = ref('');
const termInput = ref('');
const termBusy = ref(false);
const termHistory = ref([]);
const termHistIdx = ref(-1);
const termBox = ref(null);
const quickCmds = ['qm list', 'pct list', 'df -h', 'free -h', 'uptime', 'pveversion -v | head -20'];

function termHistoryNav(dir) {
  if (!termHistory.value.length) return;
  let idx = termHistIdx.value + dir;
  if (idx < -1) idx = -1;
  if (idx >= termHistory.value.length) idx = termHistory.value.length - 1;
  termHistIdx.value = idx;
  termInput.value = idx === -1 ? '' : termHistory.value[idx];
}

async function runCommand(cmd) {
  const command = (cmd || termInput.value).trim();
  if (!command || termBusy.value) return;
  termBusy.value = true;
  if (!cmd) {
    termHistory.value.push(command);
    if (termHistory.value.length > 50) termHistory.value.shift();
    termHistIdx.value = -1;
    termInput.value = '';
  }
  termOutput.value += `\nroot@pve:~# ${command}\n`;
  await nextTick(() => {
    if (termBox.value) termBox.value.scrollTop = termBox.value.scrollHeight;
  });
  try {
    const res = await props.api.post(`${API_BASE.value}/terminal`, { command });
    if (res?.success) {
      termOutput.value += (res.output || '') + (res.exit_code ? `\n[退出码 ${res.exit_code}]\n` : '\n');
    } else {
      termOutput.value += `${res?.message || res?.error || '执行失败'}\n`;
    }
  } catch (e) {
    termOutput.value += `${e?.message || '请求失败'}\n`;
  }
  await nextTick(() => {
    if (termBox.value) termBox.value.scrollTop = termBox.value.scrollHeight;
  });
  termBusy.value = false;
}

// ---------- 虚机控制台 ----------
// noVNC 需要浏览器持有 PVE 登录 cookie（SameSite 限制 iframe 内不可用，且 MP 插件 API 无 WebSocket 无法转发画面流）。
// 故 QEMU 虚机走 screendump 实时画面（后端 API+SSH，无需登录 PVE）；完整图形控制台仍用 noVNC 独立小窗。
const screenDialog = reactive({ show: false, vmid: null, name: '' });
const screenTick = ref(0);
const screenRate = ref(2);
const screenTimer = ref(null);
const screenError = ref(false);

const screenSrc = computed(() => {
  if (!screenDialog.show || !screenDialog.vmid) return '';
  const apikey = window.API_TOKEN || localStorage.getItem('api_token') || '';
  return `/api/v1/${API_BASE.value}/vm_screen?vmid=${screenDialog.vmid}&type=qemu`
    + `&apikey=${encodeURIComponent(apikey)}&t=${screenTick.value}`;
});

function startScreenTimer() {
  stopScreenTimer();
  if (screenRate.value > 0) {
    screenTimer.value = setInterval(() => { screenTick.value++; }, screenRate.value * 1000);
  }
}
function stopScreenTimer() {
  if (screenTimer.value) { clearInterval(screenTimer.value); screenTimer.value = null; }
}
watch(screenRate, startScreenTimer);

function openConsole(vm) {
  const isLxc = String(vm.type || '').toUpperCase() === 'LXC';
  if (!isLxc) {
    screenDialog.vmid = vm.vmid;
    screenDialog.name = vm.displayName || vm.name || vm.vmid;
    screenError.value = false;
    screenDialog.show = true;
    nextTick(startScreenTimer);
    return;
  }
  openNovnc(vm);
}

function consoleUrl(vm) {
  const m = monitorData.value || {};
  const apiHost = m.api_host || host.value.ip || window.location.hostname;
  const ctype = String(vm?.type || '').toUpperCase() === 'LXC' ? 'lxc' : 'kvm';
  const node = m.node ? `&node=${encodeURIComponent(m.node)}` : '';
  return `https://${apiHost}:8006/?console=${ctype}&novnc=1&vmid=${vm?.vmid}${node}&resize=off`;
}

function openNovnc(vm) {
  const m = monitorData.value || {};
  const apiHost = m.api_host || host.value.ip || window.location.hostname;
  const feat = 'popup=yes,width=1100,height=760,menubar=no,toolbar=no,location=no,status=no';

  let ticketTs = 0;
  try { ticketTs = parseInt(localStorage.getItem('pveWebLoginTs') || '0', 10) || 0; } catch {}
  const loggedIn = ticketTs && (Date.now() - ticketTs) < 2 * 3600 * 1000; // 与 PVE ticket 有效期对齐

  if (loggedIn) {
    window.open(consoleUrl(vm), `pvenovnc-${vm.vmid}`, feat);
    return;
  }
  // 首次（或超过2小时）：弹 PVE 登录页，登录后再次点击控制台直达
  try { localStorage.setItem('pveWebLoginTs', String(Date.now())); } catch {}
  window.open(`https://${apiHost}:8006/`, 'pvelogin', feat);
  showTip('已弹出 PVE 登录窗口，请先登录；登录后回到本页再次点击控制台即可打开 noVNC', 'info');
}

// ---------- 镜像模板 ----------
const tplDialog = ref(false);
const tplList = ref([]);
const tplLoading = ref(false);
const tplCounts = computed(() => ({
  iso: tplList.value.filter((f) => f.type === 'iso').length,
  ct: tplList.value.filter((f) => f.type !== 'iso').length,
}));

async function fetchTplImages() {
  tplLoading.value = true;
  try {
    const files = await props.api.get(`${API_BASE.value}/template_images`);
    tplList.value = Array.isArray(files)
      ? files.map((f) => ({ ...f, filenameWithType: `${f.filename}_${f.type}` }))
      : [];
  } catch {
    tplList.value = [];
  }
  tplLoading.value = false;
}

function openTplDialog() {
  tplDialog.value = true;
  fetchTplImages();
}

const busy = reactive({ backup: false, restore: false, del: null, dl: null, stopAll: false, cleanupLogs: false, cleanupTmp: false, clearHistory: false });

const snackbar = ref({ show: false, text: '', color: 'success' });
let timer = null;

function showTip(text, color = 'success') {
  snackbar.value = { show: true, text, color };
}

// ---------- 计算属性 ----------
// 主机信息：REST 监控数据优先，SSH pve_status 兜底
const host = computed(() => {
  const p = pve.value || {};
  const m = monitorData.value || {};
  return {
    online: p.online !== false,
    error: p.error || '',
    hostname: m.node || p.hostname || '',
    pve_version: m.pveversion || p.pve_version || '',
    cpu_model: m.cpu_model || p.cpu_model || '',
    cpu_cores: m.cpu_cores || p.cpu_cores || '',
    ip: p.ip && p.ip !== '-' ? p.ip : '',
    kernel: p.kernel || m.kversion || '',
  };
});

const hostBars = computed(() => {
  const p = pve.value || {};
  const m = monitorData.value || {};
  const mem = m.memory || {};
  const root = m.rootfs || {};
  const swap = m.swap || {};
  const fmtGB = (v) => (v == null || isNaN(v) ? '-' : (v / 1073741824).toFixed(1) + ' GB');
  const pct = (u, t) => (u != null && t > 0 ? Math.round((u / t) * 1000) / 10 : 0);
  // REST（bytes）优先；SSH pve_status 容量单位为 MB，换算为 bytes
  const cpuVal = m.cpu != null ? Math.round(m.cpu * 1000) / 10 : (p.cpu_usage ?? null);
  const toB = (v) => (v == null ? null : v * 1048576);
  const memUsed = mem.used ?? toB(p.mem_used);
  const memTotal = mem.total ?? toB(p.mem_total);
  const rootUsed = root.used ?? toB(p.disk_used);
  const rootTotal = root.total ?? toB(p.disk_total);
  const swapUsed = swap.used ?? toB(p.swap_used);
  const swapTotal = swap.total ?? toB(p.swap_total);
  // 温度合理值过滤（SSH 解析可能出垃圾值）
  const okTemp = (t) => (t != null && t >= 10 && t <= 110 ? t : null);
  const cpuTemp = okTemp(p.cpu_temp);
  return [
    {
      label: 'CPU',
      percent: cpuVal ?? 0,
      value: cpuVal != null ? cpuVal + '%' : '-',
      extra: cpuTemp != null ? cpuTemp + '°C' : '',
    },
    {
      label: '内存',
      percent: pct(memUsed, memTotal),
      value: `${fmtGB(memUsed)} / ${fmtGB(memTotal)}`,
    },
    {
      label: '根分区',
      percent: pct(rootUsed, rootTotal),
      value: `${fmtGB(rootUsed)} / ${fmtGB(rootTotal)}`,
    },
    {
      label: 'Swap',
      percent: pct(swapUsed, swapTotal),
      value: swapTotal ? `${fmtGB(swapUsed)} / ${fmtGB(swapTotal)}` : '未启用',
    },
  ];
});

function barColor(v) {
  if (v == null) return 'grey';
  if (v >= 90) return 'error';
  if (v >= 75) return 'warning';
  return 'success';
}

const vmRunning = computed(() => vmList.value.filter((v) => v.status === 'running').length);
const vmStopped = computed(() => vmList.value.filter((v) => v.status !== 'running').length);

const filteredVms = computed(() => {
  const kw = (vmSearch.value || '').trim().toLowerCase();
  if (!kw) return vmList.value;
  return vmList.value.filter((v) =>
    [v.vmid, v.displayName, v.name, v.tags].some((x) => String(x ?? '').toLowerCase().includes(kw))
  );
});

const backupCounts = computed(() => ({
  local: backupFiles.value.filter((f) => f.source === '本地备份').length,
  webdav: backupFiles.value.filter((f) => f.source === 'WebDAV备份').length,
}));

// 存储使用（来自 PVE API）
const storageBars = computed(() => {
  const fmtGB = (v) => (v == null ? '-' : (v / 1073741824).toFixed(1) + ' GB');
  return (monitorData.value?.storages || [])
    .filter((s) => s.total > 0)
    .map((s) => ({
      label: `存储 · ${s.storage} (${s.type})`,
      percent: Math.round((s.used_fraction || 0) * 100),
      value: `${fmtGB(s.used)} / ${fmtGB(s.total)}`,
    }));
});

// 最近任务列表
const taskList = computed(() => (monitorData.value?.tasks || []).map((t) => {
  const st = String(t.status || '');
  const ok = st.toUpperCase() === 'OK';
  const running = !st;
  const d = t.starttime ? new Date(t.starttime * 1000) : null;
  const timeText = d
    ? `${d.getMonth() + 1}-${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
    : '';
  return { ...t, ok, running, timeText, statusText: running ? '运行中' : (ok ? 'OK' : '失败') };
}));

// ---------- SVG 图表 ----------
function chartSeries(values, color, w = 300, h = 64, maxV = null) {
  const pts = values.map((v) => Number(v) || 0);
  if (!pts.length) return null;
  const max = maxV || Math.max(...pts, 1e-9);
  const stepX = pts.length > 1 ? w / (pts.length - 1) : 0;
  const coords = pts.map((v, i) => [i * stepX, h - Math.max(0, Math.min(1, v / max)) * (h - 4) - 2]);
  const points = coords.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
  return { points, areaPoints: `${points} ${w},${h} 0,${h}`, color };
}

function fmtChartNum(v) {
  return v >= 100 ? Math.round(v).toString() : String(Math.round(v * 10) / 10);
}

// 节点监控 6 图：CPU / 内存 / 网络进出 / 根分区 / Swap / IO等待
const monCharts = computed(() => {
  const rrd = monitorData.value?.rrd || [];
  if (!rrd.length) return [];
  const gb = 1 / 1073741824;
  const mb = 1 / 1048576;
  const num = (r, f) => Number(r[f]) || 0;
  const maxOf = (f) => Math.max(...rrd.map((r) => num(r, f)));
  const defs = [
    { key: 'cpu', title: 'CPU 使用率', unit: '%', fixedMax: 100,
      fields: [{ f: 'cpu', color: '#4f8cff', scale: 100 }] },
    { key: 'mem', title: '内存使用', unit: ' GB', fixedMax: maxOf('memtotal') * gb,
      fields: [{ f: 'memused', color: '#43b581', scale: gb }] },
    { key: 'net', title: '网络 进/出', unit: ' MB/s',
      fields: [{ f: 'netin', color: '#ef6b6b', scale: mb }, { f: 'netout', color: '#43b581', scale: mb }] },
    { key: 'root', title: '根分区已用', unit: ' GB',
      fields: [{ f: 'rootused', color: '#f59e0b', scale: gb }] },
    { key: 'swap', title: 'Swap 使用', unit: ' GB',
      fields: [{ f: 'swapused', color: '#9c27b0', scale: gb }] },
    { key: 'iowait', title: 'IO 等待', unit: '%', fixedMax: 100,
      fields: [{ f: 'iowait', color: '#e91e63', scale: 100 }] },
  ];
  return defs.map((d) => {
    const lines = [];
    for (const fd of d.fields) {
      const values = rrd.map((r) => num(r, fd.f) * fd.scale);
      const ln = chartSeries(values, fd.color, 300, 64, d.fixedMax);
      if (!ln) return null;
      lines.push(ln);
    }
    const lastVals = d.fields.map((fd) => (rrd.length ? num(rrd[rrd.length - 1], fd.f) * fd.scale : 0));
    const last = `${lastVals.map(fmtChartNum).join(' / ')}${d.unit}`;
    return { key: d.key, title: d.title, lines, last };
  }).filter(Boolean);
});

// 单虚机监控 4 图：CPU / 内存 / 网络 / 磁盘IO
const guestCharts = computed(() => {
  const rrd = guestData.value?.rrd || [];
  if (!rrd.length) return [];
  const gb = 1 / 1073741824;
  const mb = 1 / 1048576;
  const num = (r, f) => Number(r[f]) || 0;
  const maxOf = (f) => Math.max(...rrd.map((r) => num(r, f)));
  const defs = [
    { key: 'cpu', title: 'CPU 使用率', unit: '%', fixedMax: 100,
      fields: [{ f: 'cpu', color: '#4f8cff', scale: 100 }] },
    { key: 'mem', title: '内存使用', unit: ' GB', fixedMax: maxOf('maxmem') * gb,
      fields: [{ f: 'mem', color: '#43b581', scale: gb }] },
    { key: 'net', title: '网络 进/出', unit: ' MB/s',
      fields: [{ f: 'netin', color: '#ef6b6b', scale: mb }, { f: 'netout', color: '#43b581', scale: mb }] },
    { key: 'disk', title: '磁盘 读/写', unit: ' MB/s',
      fields: [{ f: 'diskread', color: '#f59e0b', scale: mb }, { f: 'diskwrite', color: '#e91e63', scale: mb }] },
  ];
  return defs.map((d) => {
    const lines = [];
    for (const fd of d.fields) {
      const values = rrd.map((r) => num(r, fd.f) * fd.scale);
      const ln = chartSeries(values, fd.color, 300, 64, d.fixedMax);
      if (!ln) return null;
      lines.push(ln);
    }
    const lastVals = d.fields.map((fd) => (rrd.length ? num(rrd[rrd.length - 1], fd.f) * fd.scale : 0));
    const last = `${lastVals.map(fmtChartNum).join(' / ')}${d.unit}`;
    return { key: d.key, title: d.title, lines, last };
  }).filter(Boolean);
});

const filteredFiles = computed(() => {
  let list = backupFiles.value;
  if (fileSource.value !== '全部') list = list.filter((f) => f.source === fileSource.value);
  const kw = (fileSearch.value || '').trim().toLowerCase();
  if (kw) list = list.filter((f) => String(f.filename || '').toLowerCase().includes(kw));
  return list;
});

function vmActions(vm) {
  if (vm.status === 'running') {
    return [
      { action: 'reboot', label: '重启', icon: 'mdi-restart', color: 'warning' },
      { action: 'stop', label: '停止', icon: 'mdi-stop', color: 'error' },
      { action: 'snapshot', label: '快照', icon: 'mdi-camera-outline', color: 'teal' },
    ];
  }
  return [{ action: 'start', label: '启动', icon: 'mdi-play', color: 'success' }];
}

function fmtUptime(sec) {
  const d = Math.floor(sec / 86400);
  const h = Math.floor((sec % 86400) / 3600);
  const m = Math.floor((sec % 3600) / 60);
  if (d) return `${d}天${h}小时`;
  if (h) return `${h}小时${m}分`;
  return `${m}分钟`;
}

// ---------- 数据拉取 ----------
// 本地缓存：上次数据立即呈现、后台静默刷新（stale-while-revalidate）
function loadCache(key) {
  try {
    const raw = localStorage.getItem(CACHE_PREFIX + key);
    if (!raw) return null;
    const obj = JSON.parse(raw);
    if (!obj || Date.now() - (obj.ts || 0) > CACHE_TTL) return null;
    return obj.data;
  } catch {
    return null;
  }
}

function saveCache(key, data) {
  try {
    localStorage.setItem(CACHE_PREFIX + key, JSON.stringify({ ts: Date.now(), data }));
  } catch {
    /* 存储失败忽略 */
  }
}

async function fetchPveStatus() {
  try {
    const data = await props.api.get(`${API_BASE.value}/pve_status`);
    pve.value = data || {};
    saveCache('pve', pve.value);
  } catch (e) {
    if (!Object.keys(pve.value).length) pve.value = loadCache('pve') || { online: false, error: e?.message || '获取失败' };
  }
}

async function fetchVmList() {
  try {
    const data = await props.api.get(`${API_BASE.value}/container_status`);
    vmList.value = Array.isArray(data) ? data : [];
    saveCache('vmlist', vmList.value);
  } catch {
    if (!vmList.value.length) vmList.value = loadCache('vmlist') || [];
    /* 请求失败保留当前数据，下次刷新重试 */
  }
}

async function fetchStatus() {
  try {
    status.value = (await props.api.get(`${API_BASE.value}/status`)) || {};
    saveCache('status', status.value);
  } catch {
    if (!Object.keys(status.value).length) status.value = loadCache('status') || {};
  }
}

async function fetchBackupFiles() {
  try {
    const files = await props.api.get(`${API_BASE.value}/available_backups`);
    backupFiles.value = Array.isArray(files) ? files : [];
    saveCache('files', backupFiles.value);
  } catch {
    if (!backupFiles.value.length) backupFiles.value = loadCache('files') || [];
  }
}

async function fetchMonitor() {
  monitorLoading.value = true;
  try {
    const data = await props.api.get(`${API_BASE.value}/monitor?timeframe=${monitorTf.value}`);
    if (data && !data.error) {
      monitorData.value = data;
      saveCache('monitor', data);
    }
  } catch {
    if (!monitorData.value) monitorData.value = loadCache('monitor');
  }
  monitorLoading.value = false;
}

async function fetchGuest() {
  if (!guestDialog.vmid) return;
  guestLoading.value = true;
  try {
    const data = await props.api.get(
      `${API_BASE.value}/guest_monitor?type=${guestDialog.type}&vmid=${guestDialog.vmid}&timeframe=${guestTf.value}`);
    guestData.value = data && !data.error ? data : null;
  } catch {
    guestData.value = null;
  }
  guestLoading.value = false;
}

async function openGuest(vm) {
  guestDialog.vmid = vm.vmid;
  guestDialog.type = vm.type === 'LXC' ? 'lxc' : 'qemu';
  guestDialog.name = vm.displayName || vm.name || vm.vmid;
  guestData.value = null;
  guestDialog.show = true;
  await fetchGuest();
}

async function refreshAll() {
  refreshing.value = true;
  await Promise.all([fetchStatus(), fetchPveStatus(), fetchVmList(), fetchBackupFiles(), fetchMonitor()]);
  refreshing.value = false;
}

function setupTimer() {
  if (timer) clearInterval(timer);
  if (refreshInterval.value > 0) timer = setInterval(refreshAll, refreshInterval.value * 1000);
}
watch(refreshInterval, setupTimer);
watch(monitorTf, fetchMonitor);
watch(guestTf, () => { if (guestDialog.show) fetchGuest(); });

// ---------- 交互 ----------
const confirmDialog = reactive({ show: false, title: '', text: '', confirm: null });
function askConfirm(key, title, text, item = null) {
  const acts = {
    delete: () => doDelete(item),
    stopAll: doStopAll,
    clearHistory: doClearHistory,
    hostReboot: () => doHostAction('reboot'),
    hostShutdown: () => doHostAction('shutdown'),
  };
  confirmDialog.title = title;
  confirmDialog.text = text;
  confirmDialog.confirm = acts[key] || null;
  confirmDialog.show = true;
}

async function runBackup() {
  busy.backup = true;
  try {
    const res = await props.api.post(`${API_BASE.value}/run_backup`, {});
    showTip(res.message || '备份任务已启动', res.success === false ? 'error' : 'success');
    await fetchStatus();
  } catch (e) {
    showTip('启动失败: ' + (e?.message || '未知错误'), 'error');
  }
  busy.backup = false;
}

async function onVmAction(vm, action) {
  if (action === 'snapshot') {
    vm._actionLoading = 'snapshot';
    try {
      const res = await props.api.post(`${API_BASE.value}/container_snapshot`, { vmid: vm.vmid, type: vm.type });
      showTip(res.message || '快照操作完成', res.success ? 'success' : 'error');
    } catch (e) {
      showTip('快照失败: ' + (e?.message || '未知错误'), 'error');
    }
    vm._actionLoading = null;
    return;
  }
  vm._actionLoading = action;
  try {
    const res = await props.api.post(`${API_BASE.value}/container_action`, {
      vmid: vm.vmid,
      type: vm.type,
      action,
    });
    showTip(res.message || `${action} 操作完成`, res.success ? 'success' : 'error');
    await fetchVmList();
  } catch (e) {
    showTip('操作失败: ' + (e?.message || '未知错误'), 'error');
  }
  vm._actionLoading = null;
}

async function doDelete(item) {
  confirmDialog.show = false;
  if (!item) return;
  busy.del = item.filename;
  try {
    const payload = { filename: item.filename, source: item.source };
    if (item.storage) payload.storage = item.storage;
    if (item.remote_dir) payload.remote_dir = item.remote_dir;
    const res = await props.api.post(`${API_BASE.value}/delete_backup`, payload);
    showTip(res.message || '删除完成', res.success ? 'success' : 'error');
    await fetchBackupFiles();
  } catch (e) {
    showTip('删除失败: ' + (e?.message || '未知错误'), 'error');
  }
  busy.del = null;
}

async function doStopAll() {
  confirmDialog.show = false;
  busy.stopAll = true;
  try {
    const res = await props.api.post(`${API_BASE.value}/stop_all_tasks`, {});
    showTip(res.message || '已停止所有任务', res.success ? 'success' : 'error');
    await fetchVmList();
  } catch (e) {
    showTip('操作失败: ' + (e?.message || '未知错误'), 'error');
  }
  busy.stopAll = false;
}

async function doClearHistory() {
  confirmDialog.show = false;
  busy.clearHistory = true;
  try {
    await props.api.post(`${API_BASE.value}/clear_history`, {});
    showTip('历史记录已清空');
  } catch (e) {
    showTip('清空失败: ' + (e?.message || '未知错误'), 'error');
  }
  busy.clearHistory = false;
}

async function doHostAction(action) {
  confirmDialog.show = false;
  try {
    const res = await props.api.post(`${API_BASE.value}/host_action`, { action });
    showTip(res.msg || res.message || '指令已下发', res.success ? 'warning' : 'error');
  } catch (e) {
    showTip('操作失败: ' + (e?.message || '未知错误'), 'error');
  }
}

async function doCleanup(path, okText) {
  const key = path === 'cleanup_logs' ? 'cleanupLogs' : 'cleanupTmp';
  busy[key] = true;
  try {
    const res = await props.api.post(`${API_BASE.value}/${path}`, {});
    showTip(res.message || okText, res.success ? 'success' : 'error');
  } catch (e) {
    showTip('清理失败: ' + (e?.message || '未知错误'), 'error');
  }
  busy[key] = false;
}

// ---------- 恢复与下载 ----------
const restoreDialog = reactive({ show: false, item: null, vmid: '' });
function askRestore(item) {
  restoreDialog.item = item;
  restoreDialog.vmid = '';
  restoreDialog.show = true;
}

async function doRestore() {
  restoreDialog.show = false;
  busy.restore = true;
  try {
    const payload = { filename: restoreDialog.item.filename, source: restoreDialog.item.source };
    if (restoreDialog.vmid) payload.vmid = restoreDialog.vmid;
    const res = await props.api.post(`${API_BASE.value}/restore`, payload);
    showTip(res.message || '恢复任务已启动', res.success === false ? 'error' : 'success');
    await fetchStatus();
  } catch (e) {
    showTip('恢复失败: ' + (e?.message || '未知错误'), 'error');
  }
  busy.restore = false;
}

async function downloadBackup(item) {
  busy.dl = item.filename;
  try {
    const res = await props.api.get(`${API_BASE.value}/token`);
    if (res && res.api_token) {
      window.API_TOKEN = res.api_token;
      localStorage.setItem('api_token', res.api_token);
    }
  } catch {
    /* 已有 token 则忽略 */
  }
  const apikey = window.API_TOKEN || localStorage.getItem('api_token') || '';
  const params = new URLSearchParams({ filename: item.filename, source: item.source });
  if (apikey) params.append('apikey', apikey);
  if (item.storage) params.append('storage', item.storage);
  if (item.remote_dir) params.append('remote_dir', item.remote_dir);
  try {
    const resp = await axios$1.get(`/api/v1/${API_BASE.value}/download_backup?` + params.toString(), {
      responseType: 'blob',
    });
    let filename = item.filename || 'backup.dat';
    const disposition = resp.headers['content-disposition'];
    if (disposition) {
      const match = disposition.match(/filename="?([^";]+)"?/);
      if (match) filename = decodeURIComponent(match[1]);
    }
    const blobUrl = window.URL.createObjectURL(new Blob([resp.data]));
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
    showTip('已开始下载: ' + filename);
  } catch (e) {
    showTip('下载失败: ' + (e?.message || '未知错误'), 'error');
  }
  busy.dl = null;
}

// ---------- 生命周期 ----------
onMounted(async () => {
  // 先用上次缓存立即呈现（2小时内有效），随后后台静默刷新
  pve.value = loadCache('pve') || {};
  status.value = loadCache('status') || {};
  vmList.value = loadCache('vmlist') || [];
  backupFiles.value = loadCache('files') || [];
  monitorData.value = loadCache('monitor');
  await refreshAll();
  setupTimer();
});

onBeforeUnmount(() => {
  if (timer) clearInterval(timer);
});

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_tooltip = _resolveComponent("v-tooltip");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_alert = _resolveComponent("v-alert");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_progress_linear = _resolveComponent("v-progress-linear");
  const _component_v_divider = _resolveComponent("v-divider");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_list_item = _resolveComponent("v-list-item");
  const _component_v_list_item_title = _resolveComponent("v-list-item-title");
  const _component_v_list = _resolveComponent("v-list");
  const _component_v_btn_toggle = _resolveComponent("v-btn-toggle");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_dialog = _resolveComponent("v-dialog");
  const _component_v_card_actions = _resolveComponent("v-card-actions");
  const _component_v_snackbar = _resolveComponent("v-snackbar");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createElementVNode("div", _hoisted_2, [
      _createVNode(_component_v_icon, {
        color: "primary",
        size: "28"
      }, {
        default: _withCtx(() => [...(_cache[50] || (_cache[50] = [
          _createTextVNode("mdi-server", -1)
        ]))]),
        _: 1
      }),
      _cache[55] || (_cache[55] = _createElementVNode("span", { class: "text-h5 font-weight-bold" }, "PVE 守护神", -1)),
      _createVNode(_component_v_chip, {
        color: host.value.online ? 'success' : 'error',
        size: "small",
        variant: "tonal"
      }, {
        default: _withCtx(() => [
          _createTextVNode(_toDisplayString(host.value.online ? '已连接' : '未连接'), 1)
        ]),
        _: 1
      }, 8, ["color"]),
      (host.value.pve_version)
        ? (_openBlock(), _createBlock(_component_v_chip, {
            key: 0,
            size: "small",
            variant: "tonal",
            class: "text-caption"
          }, {
            default: _withCtx(() => [
              _createTextVNode(" PVE " + _toDisplayString(host.value.pve_version), 1)
            ]),
            _: 1
          }))
        : _createCommentVNode("", true),
      _createVNode(_component_v_spacer),
      _createVNode(_component_v_tooltip, {
        text: "查看 PVE 上的 ISO 镜像与 CT 模板",
        location: "bottom"
      }, {
        activator: _withCtx(({ props: tip }) => [
          _createVNode(_component_v_btn, _mergeProps(tip, {
            size: "small",
            variant: "tonal",
            color: "deep-purple",
            disabled: !status.value.cleanup_template_images,
            onClick: openTplDialog
          }), {
            default: _withCtx(() => [
              _createVNode(_component_v_icon, {
                size: "16",
                class: "mr-1"
              }, {
                default: _withCtx(() => [...(_cache[51] || (_cache[51] = [
                  _createTextVNode("mdi-cube-outline", -1)
                ]))]),
                _: 1
              }),
              _cache[52] || (_cache[52] = _createTextVNode("镜像模板 ", -1))
            ]),
            _: 1
          }, 16, ["disabled"])
        ]),
        _: 1
      }),
      _createVNode(_component_v_select, {
        modelValue: refreshInterval.value,
        "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((refreshInterval).value = $event)),
        items: refreshOptions,
        density: "compact",
        variant: "outlined",
        "hide-details": "",
        label: "刷新间隔",
        style: {"max-width":"130px"}
      }, null, 8, ["modelValue"]),
      _createVNode(_component_v_btn, {
        size: "small",
        variant: "tonal",
        color: "primary",
        loading: refreshing.value,
        onClick: refreshAll
      }, {
        default: _withCtx(() => [
          _createVNode(_component_v_icon, {
            size: "16",
            class: "mr-1"
          }, {
            default: _withCtx(() => [...(_cache[53] || (_cache[53] = [
              _createTextVNode("mdi-refresh", -1)
            ]))]),
            _: 1
          }),
          _cache[54] || (_cache[54] = _createTextVNode(" 刷新 ", -1))
        ]),
        _: 1
      }, 8, ["loading"])
    ]),
    (!host.value.online && host.value.error)
      ? (_openBlock(), _createBlock(_component_v_alert, {
          key: 0,
          type: "error",
          variant: "tonal",
          density: "compact",
          class: "mb-4"
        }, {
          default: _withCtx(() => [
            _createTextVNode(_toDisplayString(host.value.error), 1)
          ]),
          _: 1
        }))
      : _createCommentVNode("", true),
    _createVNode(_component_v_row, null, {
      default: _withCtx(() => [
        _createVNode(_component_v_col, {
          cols: "12",
          md: "6"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              class: _normalizeClass([{ 'card-collapsed': collapsed.host }, collapsed.host ? '' : 'fill-height'])
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_title, {
                  class: "d-flex align-center flex-wrap ga-1 cursor-pointer",
                  onClick: _cache[6] || (_cache[6] = $event => (collapsed.host = !collapsed.host))
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_icon, {
                      color: "info",
                      size: "22",
                      class: "mr-2"
                    }, {
                      default: _withCtx(() => [...(_cache[56] || (_cache[56] = [
                        _createTextVNode("mdi-cpu-64-bit", -1)
                      ]))]),
                      _: 1
                    }),
                    _cache[57] || (_cache[57] = _createElementVNode("span", null, "主机概况", -1)),
                    (host.value.hostname)
                      ? (_openBlock(), _createBlock(_component_v_chip, {
                          key: 0,
                          size: "x-small",
                          variant: "tonal",
                          color: "info",
                          class: "ml-2"
                        }, {
                          default: _withCtx(() => [
                            _createTextVNode(_toDisplayString(host.value.hostname), 1)
                          ]),
                          _: 1
                        }))
                      : _createCommentVNode("", true),
                    _createVNode(_component_v_spacer),
                    _createVNode(_component_v_tooltip, {
                      text: "清理系统日志",
                      location: "top"
                    }, {
                      activator: _withCtx(({ props: tip }) => [
                        _createVNode(_component_v_btn, _mergeProps(tip, {
                          size: "small",
                          variant: "text",
                          color: "teal",
                          icon: "mdi-broom",
                          loading: busy.cleanupLogs,
                          onClick: _cache[1] || (_cache[1] = _withModifiers($event => (doCleanup('cleanup_logs', '系统日志清理完成')), ["stop"]))
                        }), null, 16, ["loading"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_tooltip, {
                      text: "清理临时空间",
                      location: "top"
                    }, {
                      activator: _withCtx(({ props: tip }) => [
                        _createVNode(_component_v_btn, _mergeProps(tip, {
                          size: "small",
                          variant: "text",
                          color: "teal",
                          icon: "mdi-delete-sweep-outline",
                          loading: busy.cleanupTmp,
                          onClick: _cache[2] || (_cache[2] = _withModifiers($event => (doCleanup('cleanup_tmp', '临时空间清理完成')), ["stop"]))
                        }), null, 16, ["loading"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_tooltip, {
                      text: "重启主机",
                      location: "top"
                    }, {
                      activator: _withCtx(({ props: tip }) => [
                        _createVNode(_component_v_btn, _mergeProps(tip, {
                          size: "small",
                          variant: "text",
                          color: "warning",
                          icon: "mdi-restart",
                          onClick: _cache[3] || (_cache[3] = _withModifiers($event => (askConfirm('hostReboot', '重启 PVE 主机', '确认重启 PVE 主机？所有虚拟机将受影响！')), ["stop"]))
                        }), null, 16)
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_tooltip, {
                      text: "关闭主机",
                      location: "top"
                    }, {
                      activator: _withCtx(({ props: tip }) => [
                        _createVNode(_component_v_btn, _mergeProps(tip, {
                          size: "small",
                          variant: "text",
                          color: "error",
                          icon: "mdi-power",
                          onClick: _cache[4] || (_cache[4] = _withModifiers($event => (askConfirm('hostShutdown', '关闭 PVE 主机', '确认关闭 PVE 主机？所有虚拟机将关机！')), ["stop"]))
                        }), null, 16)
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_tooltip, {
                      text: "宿主机终端",
                      location: "top"
                    }, {
                      activator: _withCtx(({ props: tip }) => [
                        _createVNode(_component_v_btn, _mergeProps(tip, {
                          size: "small",
                          variant: "text",
                          color: "deep-purple",
                          icon: "mdi-console",
                          onClick: _cache[5] || (_cache[5] = _withModifiers($event => (termDialog.value = true), ["stop"]))
                        }), null, 16)
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_icon, {
                      size: "18",
                      class: "ml-1"
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode(_toDisplayString(collapsed.host ? 'mdi-chevron-down' : 'mdi-chevron-up'), 1)
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                (!collapsed.host)
                  ? (_openBlock(), _createBlock(_component_v_card_text, { key: 0 }, {
                      default: _withCtx(() => [
                        _createElementVNode("div", _hoisted_3, [
                          _createTextVNode(_toDisplayString(host.value.cpu_model || 'CPU 未知') + " · " + _toDisplayString(host.value.cpu_cores || '?') + " 核 ", 1),
                          (host.value.ip)
                            ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, [
                                _createTextVNode(" · " + _toDisplayString(host.value.ip), 1)
                              ], 64))
                            : _createCommentVNode("", true),
                          (host.value.kernel)
                            ? (_openBlock(), _createElementBlock(_Fragment, { key: 1 }, [
                                _createTextVNode(" · " + _toDisplayString(host.value.kernel), 1)
                              ], 64))
                            : _createCommentVNode("", true)
                        ]),
                        (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(hostBars.value, (bar) => {
                          return (_openBlock(), _createElementBlock(_Fragment, {
                            key: bar.label
                          }, [
                            _createElementVNode("div", _hoisted_4, [
                              _createElementVNode("span", null, [
                                _createTextVNode(_toDisplayString(bar.label), 1),
                                (bar.extra)
                                  ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, [
                                      _createTextVNode(" · " + _toDisplayString(bar.extra), 1)
                                    ], 64))
                                  : _createCommentVNode("", true)
                              ]),
                              _createElementVNode("span", _hoisted_5, _toDisplayString(bar.value), 1)
                            ]),
                            _createVNode(_component_v_progress_linear, {
                              "model-value": bar.percent,
                              rounded: "",
                              height: "8",
                              class: "mt-1",
                              color: barColor(bar.percent)
                            }, null, 8, ["model-value", "color"])
                          ], 64))
                        }), 128)),
                        (storageBars.value.length)
                          ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, [
                              _createVNode(_component_v_divider, { class: "my-2" }),
                              (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(storageBars.value, (bar) => {
                                return (_openBlock(), _createElementBlock(_Fragment, {
                                  key: bar.label
                                }, [
                                  _createElementVNode("div", _hoisted_6, [
                                    _createElementVNode("span", null, _toDisplayString(bar.label), 1),
                                    _createElementVNode("span", _hoisted_7, _toDisplayString(bar.value), 1)
                                  ]),
                                  _createVNode(_component_v_progress_linear, {
                                    "model-value": bar.percent,
                                    rounded: "",
                                    height: "8",
                                    class: "mt-1",
                                    color: barColor(bar.percent)
                                  }, null, 8, ["model-value", "color"])
                                ], 64))
                              }), 128))
                            ], 64))
                          : _createCommentVNode("", true)
                      ]),
                      _: 1
                    }))
                  : _createCommentVNode("", true)
              ]),
              _: 1
            }, 8, ["class"])
          ]),
          _: 1
        }),
        _createVNode(_component_v_col, {
          cols: "12",
          md: "6"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              class: _normalizeClass([{ 'card-collapsed': collapsed.tasks }, collapsed.tasks ? '' : 'fill-height'])
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_title, {
                  class: "d-flex align-center cursor-pointer",
                  onClick: _cache[7] || (_cache[7] = $event => (collapsed.tasks = !collapsed.tasks))
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_icon, {
                      color: "indigo",
                      size: "22",
                      class: "mr-2"
                    }, {
                      default: _withCtx(() => [...(_cache[58] || (_cache[58] = [
                        _createTextVNode("mdi-format-list-bulleted", -1)
                      ]))]),
                      _: 1
                    }),
                    _cache[59] || (_cache[59] = _createElementVNode("span", null, "最近任务", -1)),
                    _createVNode(_component_v_spacer),
                    _createVNode(_component_v_icon, { size: "18" }, {
                      default: _withCtx(() => [
                        _createTextVNode(_toDisplayString(collapsed.tasks ? 'mdi-chevron-down' : 'mdi-chevron-up'), 1)
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                (!collapsed.tasks)
                  ? (_openBlock(), _createBlock(_component_v_card_text, {
                      key: 0,
                      class: "task-list-body"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_list, {
                          density: "compact",
                          class: "py-0"
                        }, {
                          default: _withCtx(() => [
                            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(taskList.value, (t) => {
                              return (_openBlock(), _createBlock(_component_v_list_item, {
                                key: t.upid,
                                class: "px-0"
                              }, {
                                prepend: _withCtx(() => [
                                  _createVNode(_component_v_icon, {
                                    size: "18",
                                    color: t.running ? 'warning' : (t.ok ? 'success' : 'error')
                                  }, {
                                    default: _withCtx(() => [
                                      _createTextVNode(_toDisplayString(t.running ? 'mdi-progress-clock' : (t.ok ? 'mdi-check-circle' : 'mdi-alert-circle')), 1)
                                    ]),
                                    _: 2
                                  }, 1032, ["color"])
                                ]),
                                append: _withCtx(() => [
                                  _createElementVNode("span", {
                                    class: _normalizeClass(["text-caption", t.running ? 'text-warning' : (t.ok ? 'text-success' : 'text-error')])
                                  }, _toDisplayString(t.statusText), 3)
                                ]),
                                default: _withCtx(() => [
                                  _createElementVNode("div", _hoisted_8, [
                                    _createElementVNode("span", _hoisted_9, _toDisplayString(t.desc), 1),
                                    (t.vmid)
                                      ? (_openBlock(), _createBlock(_component_v_chip, {
                                          key: 0,
                                          size: "x-small",
                                          variant: "tonal",
                                          color: "info"
                                        }, {
                                          default: _withCtx(() => [
                                            _createTextVNode("#" + _toDisplayString(t.vmid), 1)
                                          ]),
                                          _: 2
                                        }, 1024))
                                      : _createCommentVNode("", true),
                                    _createElementVNode("span", _hoisted_10, _toDisplayString(t.timeText), 1)
                                  ])
                                ]),
                                _: 2
                              }, 1024))
                            }), 128)),
                            (!taskList.value.length)
                              ? (_openBlock(), _createBlock(_component_v_list_item, { key: 0 }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_list_item_title, { class: "text-caption text-medium-emphasis text-center py-2" }, {
                                      default: _withCtx(() => [
                                        _createTextVNode(_toDisplayString(monitorLoading.value ? '加载中...' : '暂无任务记录'), 1)
                                      ]),
                                      _: 1
                                    })
                                  ]),
                                  _: 1
                                }))
                              : _createCommentVNode("", true)
                          ]),
                          _: 1
                        })
                      ]),
                      _: 1
                    }))
                  : _createCommentVNode("", true)
              ]),
              _: 1
            }, 8, ["class"])
          ]),
          _: 1
        }),
        _createVNode(_component_v_col, { cols: "12" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              class: _normalizeClass({ 'card-collapsed': collapsed.mon })
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_title, {
                  class: "d-flex align-center flex-wrap ga-2 cursor-pointer",
                  onClick: _cache[10] || (_cache[10] = $event => (collapsed.mon = !collapsed.mon))
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_icon, {
                      color: "primary",
                      size: "22",
                      class: "mr-1"
                    }, {
                      default: _withCtx(() => [...(_cache[60] || (_cache[60] = [
                        _createTextVNode("mdi-chart-areaspline", -1)
                      ]))]),
                      _: 1
                    }),
                    _cache[65] || (_cache[65] = _createElementVNode("span", null, "性能监控", -1)),
                    _createVNode(_component_v_spacer),
                    _createVNode(_component_v_btn_toggle, {
                      modelValue: monitorTf.value,
                      "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((monitorTf).value = $event)),
                      mandatory: "",
                      density: "compact",
                      variant: "outlined",
                      divided: "",
                      onClick: _cache[9] || (_cache[9] = _withModifiers(() => {}, ["stop"]))
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_btn, {
                          value: "hour",
                          size: "small"
                        }, {
                          default: _withCtx(() => [...(_cache[61] || (_cache[61] = [
                            _createTextVNode("小时", -1)
                          ]))]),
                          _: 1
                        }),
                        _createVNode(_component_v_btn, {
                          value: "day",
                          size: "small"
                        }, {
                          default: _withCtx(() => [...(_cache[62] || (_cache[62] = [
                            _createTextVNode("天", -1)
                          ]))]),
                          _: 1
                        }),
                        _createVNode(_component_v_btn, {
                          value: "week",
                          size: "small"
                        }, {
                          default: _withCtx(() => [...(_cache[63] || (_cache[63] = [
                            _createTextVNode("周", -1)
                          ]))]),
                          _: 1
                        }),
                        _createVNode(_component_v_btn, {
                          value: "month",
                          size: "small"
                        }, {
                          default: _withCtx(() => [...(_cache[64] || (_cache[64] = [
                            _createTextVNode("月", -1)
                          ]))]),
                          _: 1
                        })
                      ]),
                      _: 1
                    }, 8, ["modelValue"]),
                    _createVNode(_component_v_icon, { size: "18" }, {
                      default: _withCtx(() => [
                        _createTextVNode(_toDisplayString(collapsed.mon ? 'mdi-chevron-down' : 'mdi-chevron-up'), 1)
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                (!collapsed.mon)
                  ? (_openBlock(), _createBlock(_component_v_card_text, { key: 0 }, {
                      default: _withCtx(() => [
                        (monitorLoading.value)
                          ? (_openBlock(), _createBlock(_component_v_progress_linear, {
                              key: 0,
                              indeterminate: "",
                              height: "2",
                              color: "primary",
                              class: "mb-2"
                            }))
                          : _createCommentVNode("", true),
                        (monCharts.value.length)
                          ? (_openBlock(), _createElementBlock("div", _hoisted_11, [
                              (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(monCharts.value, (ch) => {
                                return (_openBlock(), _createElementBlock("div", {
                                  key: ch.key,
                                  class: "chart-cell"
                                }, [
                                  _createElementVNode("div", _hoisted_12, [
                                    _createElementVNode("span", null, _toDisplayString(ch.title), 1),
                                    _createElementVNode("span", {
                                      class: "font-weight-bold",
                                      style: _normalizeStyle({ color: ch.lines.length > 1 ? '' : ch.lines[0].color })
                                    }, _toDisplayString(ch.last), 5)
                                  ]),
                                  (_openBlock(), _createElementBlock("svg", _hoisted_13, [
                                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(ch.lines, (ln, i) => {
                                      return (_openBlock(), _createElementBlock(_Fragment, { key: i }, [
                                        _createElementVNode("polygon", {
                                          points: ln.areaPoints,
                                          fill: ln.color,
                                          opacity: "0.12",
                                          stroke: "none"
                                        }, null, 8, _hoisted_14),
                                        _createElementVNode("polyline", {
                                          points: ln.points,
                                          fill: "none",
                                          stroke: ln.color,
                                          "stroke-width": "1.6"
                                        }, null, 8, _hoisted_15)
                                      ], 64))
                                    }), 128))
                                  ]))
                                ]))
                              }), 128))
                            ]))
                          : (_openBlock(), _createElementBlock("div", _hoisted_16, _toDisplayString(monitorLoading.value ? '加载中...' : '暂无监控数据（请检查 PVE API 端口 8006 是否可达）'), 1))
                      ]),
                      _: 1
                    }))
                  : _createCommentVNode("", true)
              ]),
              _: 1
            }, 8, ["class"])
          ]),
          _: 1
        }),
        _createVNode(_component_v_col, { cols: "12" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              class: _normalizeClass({ 'card-collapsed': collapsed.vm })
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_title, {
                  class: "d-flex align-center flex-wrap ga-2 cursor-pointer",
                  onClick: _cache[14] || (_cache[14] = $event => (collapsed.vm = !collapsed.vm))
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_icon, {
                      color: "teal",
                      size: "22",
                      class: "mr-1"
                    }, {
                      default: _withCtx(() => [...(_cache[66] || (_cache[66] = [
                        _createTextVNode("mdi-monitor-multiple", -1)
                      ]))]),
                      _: 1
                    }),
                    _cache[69] || (_cache[69] = _createElementVNode("span", null, "虚拟机 / 容器", -1)),
                    _createVNode(_component_v_chip, {
                      size: "x-small",
                      color: "success",
                      variant: "tonal"
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode("运行 " + _toDisplayString(vmRunning.value), 1)
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_chip, {
                      size: "x-small",
                      color: "grey",
                      variant: "tonal"
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode("停止 " + _toDisplayString(vmStopped.value), 1)
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_spacer),
                    _createVNode(_component_v_text_field, {
                      modelValue: vmSearch.value,
                      "onUpdate:modelValue": _cache[11] || (_cache[11] = $event => ((vmSearch).value = $event)),
                      density: "compact",
                      variant: "outlined",
                      "hide-details": "",
                      clearable: "",
                      placeholder: "搜索 ID / 名称 / 标签",
                      "prepend-inner-icon": "mdi-magnify",
                      style: {"max-width":"220px"},
                      onClick: _cache[12] || (_cache[12] = _withModifiers(() => {}, ["stop"]))
                    }, null, 8, ["modelValue"]),
                    _createVNode(_component_v_btn, {
                      size: "small",
                      variant: "text",
                      color: "error",
                      loading: busy.stopAll,
                      onClick: _cache[13] || (_cache[13] = _withModifiers($event => (askConfirm('stopAll', '停止所有任务', '确认停止 PVE 上所有正在运行的任务？')), ["stop"]))
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, {
                          size: "16",
                          class: "mr-1"
                        }, {
                          default: _withCtx(() => [...(_cache[67] || (_cache[67] = [
                            _createTextVNode("mdi-stop-circle-outline", -1)
                          ]))]),
                          _: 1
                        }),
                        _cache[68] || (_cache[68] = _createTextVNode("全部停止 ", -1))
                      ]),
                      _: 1
                    }, 8, ["loading"]),
                    _createVNode(_component_v_icon, { size: "18" }, {
                      default: _withCtx(() => [
                        _createTextVNode(_toDisplayString(collapsed.vm ? 'mdi-chevron-down' : 'mdi-chevron-up'), 1)
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                (!collapsed.vm)
                  ? (_openBlock(), _createBlock(_component_v_card_text, { key: 0 }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_list, {
                          density: "compact",
                          class: "py-0"
                        }, {
                          default: _withCtx(() => [
                            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(filteredVms.value, (vm) => {
                              return (_openBlock(), _createBlock(_component_v_list_item, {
                                key: vm.vmid + vm.type,
                                class: "px-0 vm-row"
                              }, {
                                prepend: _withCtx(() => [
                                  _createVNode(_component_v_icon, {
                                    size: "20",
                                    color: vm.status === 'running' ? 'success' : 'grey'
                                  }, {
                                    default: _withCtx(() => [
                                      _createTextVNode(_toDisplayString(vm.type === 'LXC' ? 'mdi-cube-outline' : 'mdi-server'), 1)
                                    ]),
                                    _: 2
                                  }, 1032, ["color"])
                                ]),
                                append: _withCtx(() => [
                                  _createElementVNode("div", _hoisted_21, [
                                    _createVNode(_component_v_tooltip, {
                                      text: "noVNC 控制台",
                                      location: "top"
                                    }, {
                                      activator: _withCtx(({ props: tip }) => [
                                        _createVNode(_component_v_btn, _mergeProps({ ref_for: true }, tip, {
                                          size: "x-small",
                                          variant: "text",
                                          color: "deep-purple",
                                          onClick: $event => (openConsole(vm))
                                        }), {
                                          default: _withCtx(() => [
                                            _createVNode(_component_v_icon, { size: "16" }, {
                                              default: _withCtx(() => [...(_cache[70] || (_cache[70] = [
                                                _createTextVNode("mdi-console", -1)
                                              ]))]),
                                              _: 1
                                            })
                                          ]),
                                          _: 1
                                        }, 16, ["onClick"])
                                      ]),
                                      _: 2
                                    }, 1024),
                                    _createVNode(_component_v_tooltip, {
                                      text: "监控图表",
                                      location: "top"
                                    }, {
                                      activator: _withCtx(({ props: tip }) => [
                                        _createVNode(_component_v_btn, _mergeProps({ ref_for: true }, tip, {
                                          size: "x-small",
                                          variant: "text",
                                          color: "primary",
                                          onClick: $event => (openGuest(vm))
                                        }), {
                                          default: _withCtx(() => [
                                            _createVNode(_component_v_icon, { size: "16" }, {
                                              default: _withCtx(() => [...(_cache[71] || (_cache[71] = [
                                                _createTextVNode("mdi-chart-line", -1)
                                              ]))]),
                                              _: 1
                                            })
                                          ]),
                                          _: 1
                                        }, 16, ["onClick"])
                                      ]),
                                      _: 2
                                    }, 1024),
                                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(vmActions(vm), (act) => {
                                      return (_openBlock(), _createBlock(_component_v_tooltip, {
                                        key: act.action,
                                        text: act.label,
                                        location: "top"
                                      }, {
                                        activator: _withCtx(({ props: tip }) => [
                                          _createVNode(_component_v_btn, _mergeProps({ ref_for: true }, tip, {
                                            size: "x-small",
                                            variant: "text",
                                            color: act.color,
                                            loading: vm._actionLoading === act.action,
                                            onClick: $event => (onVmAction(vm, act.action))
                                          }), {
                                            default: _withCtx(() => [
                                              _createVNode(_component_v_icon, { size: "16" }, {
                                                default: _withCtx(() => [
                                                  _createTextVNode(_toDisplayString(act.icon), 1)
                                                ]),
                                                _: 2
                                              }, 1024)
                                            ]),
                                            _: 2
                                          }, 1040, ["color", "loading", "onClick"])
                                        ]),
                                        _: 2
                                      }, 1032, ["text"]))
                                    }), 128))
                                  ])
                                ]),
                                default: _withCtx(() => [
                                  _createElementVNode("div", _hoisted_17, [
                                    _createElementVNode("span", _hoisted_18, _toDisplayString(vm.displayName || vm.name || vm.vmid), 1),
                                    _createElementVNode("span", _hoisted_19, "#" + _toDisplayString(vm.vmid) + " · " + _toDisplayString(vm.type), 1),
                                    _createVNode(_component_v_chip, {
                                      size: "x-small",
                                      color: vm.status === 'running' ? 'success' : 'grey',
                                      variant: "tonal"
                                    }, {
                                      default: _withCtx(() => [
                                        _createTextVNode(_toDisplayString(vm.status === 'running' ? '运行中' : '已停止'), 1)
                                      ]),
                                      _: 2
                                    }, 1032, ["color"]),
                                    (vm.status === 'running' && vm.uptime)
                                      ? (_openBlock(), _createElementBlock("span", _hoisted_20, _toDisplayString(fmtUptime(vm.uptime)), 1))
                                      : _createCommentVNode("", true)
                                  ])
                                ]),
                                _: 2
                              }, 1024))
                            }), 128)),
                            (!filteredVms.value.length)
                              ? (_openBlock(), _createBlock(_component_v_list_item, { key: 0 }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_list_item_title, { class: "text-caption text-medium-emphasis text-center py-2" }, {
                                      default: _withCtx(() => [
                                        _createTextVNode(_toDisplayString(vmList.value.length ? '没有匹配的虚拟机 / 容器' : '暂无数据'), 1)
                                      ]),
                                      _: 1
                                    })
                                  ]),
                                  _: 1
                                }))
                              : _createCommentVNode("", true)
                          ]),
                          _: 1
                        })
                      ]),
                      _: 1
                    }))
                  : _createCommentVNode("", true)
              ]),
              _: 1
            }, 8, ["class"])
          ]),
          _: 1
        }),
        _createVNode(_component_v_col, { cols: "12" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, {
              class: _normalizeClass({ 'card-collapsed': collapsed.files })
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_title, {
                  class: "d-flex align-center flex-wrap ga-2 cursor-pointer",
                  onClick: _cache[20] || (_cache[20] = $event => (collapsed.files = !collapsed.files))
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_icon, {
                      color: "amber-darken-2",
                      size: "22",
                      class: "mr-1"
                    }, {
                      default: _withCtx(() => [...(_cache[72] || (_cache[72] = [
                        _createTextVNode("mdi-file-multiple-outline", -1)
                      ]))]),
                      _: 1
                    }),
                    _cache[76] || (_cache[76] = _createElementVNode("span", null, "备份文件", -1)),
                    _createVNode(_component_v_chip, {
                      size: "x-small",
                      variant: "tonal",
                      color: "info"
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode("本地 " + _toDisplayString(backupCounts.value.local), 1)
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_chip, {
                      size: "x-small",
                      variant: "tonal",
                      color: "deep-purple"
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode("WebDAV " + _toDisplayString(backupCounts.value.webdav), 1)
                      ]),
                      _: 1
                    }),
                    (status.value.backup_activity || status.value.restore_activity)
                      ? (_openBlock(), _createBlock(_component_v_chip, {
                          key: 0,
                          size: "x-small",
                          color: "warning",
                          variant: "tonal"
                        }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_icon, {
                              size: "12",
                              class: "mr-1"
                            }, {
                              default: _withCtx(() => [...(_cache[73] || (_cache[73] = [
                                _createTextVNode("mdi-progress-clock", -1)
                              ]))]),
                              _: 1
                            }),
                            _createTextVNode(_toDisplayString(status.value.backup_activity ? '备份中' : '恢复中'), 1)
                          ]),
                          _: 1
                        }))
                      : (status.value.enabled && status.value.next_run_time)
                        ? (_openBlock(), _createBlock(_component_v_chip, {
                            key: 1,
                            size: "x-small",
                            color: "success",
                            variant: "tonal",
                            "prepend-icon": "mdi-clock-outline"
                          }, {
                            default: _withCtx(() => [
                              _createTextVNode(" 下次：" + _toDisplayString(status.value.next_run_time), 1)
                            ]),
                            _: 1
                          }))
                        : _createCommentVNode("", true),
                    _createVNode(_component_v_spacer),
                    _createVNode(_component_v_btn, {
                      size: "small",
                      variant: "tonal",
                      color: "primary",
                      loading: busy.backup,
                      onClick: _withModifiers(runBackup, ["stop"])
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, {
                          size: "16",
                          class: "mr-1"
                        }, {
                          default: _withCtx(() => [...(_cache[74] || (_cache[74] = [
                            _createTextVNode("mdi-play-circle-outline", -1)
                          ]))]),
                          _: 1
                        }),
                        _cache[75] || (_cache[75] = _createTextVNode("立即备份 ", -1))
                      ]),
                      _: 1
                    }, 8, ["loading"]),
                    _createVNode(_component_v_tooltip, {
                      text: "清空备份/恢复历史",
                      location: "top"
                    }, {
                      activator: _withCtx(({ props: tip }) => [
                        _createVNode(_component_v_btn, _mergeProps(tip, {
                          size: "small",
                          variant: "text",
                          color: "error",
                          icon: "mdi-history",
                          loading: busy.clearHistory,
                          onClick: _cache[15] || (_cache[15] = _withModifiers($event => (askConfirm('clearHistory', '清空历史记录', '确认清空所有备份与恢复历史记录？')), ["stop"]))
                        }), null, 16, ["loading"])
                      ]),
                      _: 1
                    }),
                    _createVNode(_component_v_select, {
                      modelValue: fileSource.value,
                      "onUpdate:modelValue": _cache[16] || (_cache[16] = $event => ((fileSource).value = $event)),
                      items: ['全部', '本地备份', 'WebDAV备份'],
                      density: "compact",
                      variant: "outlined",
                      "hide-details": "",
                      style: {"max-width":"140px"},
                      onClick: _cache[17] || (_cache[17] = _withModifiers(() => {}, ["stop"]))
                    }, null, 8, ["modelValue"]),
                    _createVNode(_component_v_text_field, {
                      modelValue: fileSearch.value,
                      "onUpdate:modelValue": _cache[18] || (_cache[18] = $event => ((fileSearch).value = $event)),
                      density: "compact",
                      variant: "outlined",
                      "hide-details": "",
                      clearable: "",
                      placeholder: "搜索文件名",
                      "prepend-inner-icon": "mdi-magnify",
                      style: {"max-width":"200px"},
                      onClick: _cache[19] || (_cache[19] = _withModifiers(() => {}, ["stop"]))
                    }, null, 8, ["modelValue"]),
                    _createVNode(_component_v_icon, { size: "18" }, {
                      default: _withCtx(() => [
                        _createTextVNode(_toDisplayString(collapsed.files ? 'mdi-chevron-down' : 'mdi-chevron-up'), 1)
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                (!collapsed.files)
                  ? (_openBlock(), _createBlock(_component_v_card_text, { key: 0 }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_list, {
                          density: "compact",
                          class: "py-0"
                        }, {
                          default: _withCtx(() => [
                            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(filteredFiles.value, (f) => {
                              return (_openBlock(), _createBlock(_component_v_list_item, {
                                key: f.source + f.filename,
                                class: "px-0"
                              }, {
                                prepend: _withCtx(() => [
                                  _createVNode(_component_v_icon, {
                                    size: "20",
                                    color: f.source === 'WebDAV备份' ? 'deep-purple' : 'primary'
                                  }, {
                                    default: _withCtx(() => [
                                      _createTextVNode(_toDisplayString(f.source === 'WebDAV备份' ? 'mdi-cloud-outline' : 'mdi-harddisk'), 1)
                                    ]),
                                    _: 2
                                  }, 1032, ["color"])
                                ]),
                                append: _withCtx(() => [
                                  _createElementVNode("div", _hoisted_25, [
                                    _createVNode(_component_v_tooltip, {
                                      text: "下载",
                                      location: "top"
                                    }, {
                                      activator: _withCtx(({ props: tip }) => [
                                        _createVNode(_component_v_btn, _mergeProps({ ref_for: true }, tip, {
                                          size: "x-small",
                                          variant: "text",
                                          color: "primary",
                                          loading: busy.dl === f.filename,
                                          onClick: $event => (downloadBackup(f))
                                        }), {
                                          default: _withCtx(() => [
                                            _createVNode(_component_v_icon, { size: "16" }, {
                                              default: _withCtx(() => [...(_cache[77] || (_cache[77] = [
                                                _createTextVNode("mdi-download", -1)
                                              ]))]),
                                              _: 1
                                            })
                                          ]),
                                          _: 1
                                        }, 16, ["loading", "onClick"])
                                      ]),
                                      _: 2
                                    }, 1024),
                                    _createVNode(_component_v_tooltip, {
                                      text: "恢复",
                                      location: "top"
                                    }, {
                                      activator: _withCtx(({ props: tip }) => [
                                        _createVNode(_component_v_btn, _mergeProps({ ref_for: true }, tip, {
                                          size: "x-small",
                                          variant: "text",
                                          color: "deep-purple",
                                          onClick: $event => (askRestore(f))
                                        }), {
                                          default: _withCtx(() => [
                                            _createVNode(_component_v_icon, { size: "16" }, {
                                              default: _withCtx(() => [...(_cache[78] || (_cache[78] = [
                                                _createTextVNode("mdi-restore", -1)
                                              ]))]),
                                              _: 1
                                            })
                                          ]),
                                          _: 1
                                        }, 16, ["onClick"])
                                      ]),
                                      _: 2
                                    }, 1024),
                                    _createVNode(_component_v_tooltip, {
                                      text: "删除",
                                      location: "top"
                                    }, {
                                      activator: _withCtx(({ props: tip }) => [
                                        _createVNode(_component_v_btn, _mergeProps({ ref_for: true }, tip, {
                                          size: "x-small",
                                          variant: "text",
                                          color: "error",
                                          loading: busy.del === f.filename,
                                          onClick: $event => (askConfirm('delete', '删除备份', `确认删除 ${f.source} 中的 ${f.filename}？此操作不可恢复！`, f))
                                        }), {
                                          default: _withCtx(() => [
                                            _createVNode(_component_v_icon, { size: "16" }, {
                                              default: _withCtx(() => [...(_cache[79] || (_cache[79] = [
                                                _createTextVNode("mdi-delete-outline", -1)
                                              ]))]),
                                              _: 1
                                            })
                                          ]),
                                          _: 1
                                        }, 16, ["loading", "onClick"])
                                      ]),
                                      _: 2
                                    }, 1024)
                                  ])
                                ]),
                                default: _withCtx(() => [
                                  _createElementVNode("div", _hoisted_22, [
                                    _createElementVNode("span", {
                                      class: "text-body-2 text-truncate",
                                      title: f.filename
                                    }, _toDisplayString(f.filename), 9, _hoisted_23),
                                    _createElementVNode("span", _hoisted_24, _toDisplayString(f.size_mb) + " MB · " + _toDisplayString(f.date) + " " + _toDisplayString(f.time), 1)
                                  ])
                                ]),
                                _: 2
                              }, 1024))
                            }), 128)),
                            (!filteredFiles.value.length)
                              ? (_openBlock(), _createBlock(_component_v_list_item, { key: 0 }, {
                                  default: _withCtx(() => [
                                    _createVNode(_component_v_list_item_title, { class: "text-caption text-medium-emphasis text-center py-2" }, {
                                      default: _withCtx(() => [
                                        _createTextVNode(_toDisplayString(backupFiles.value.length ? '没有匹配的备份文件' : '暂无备份文件'), 1)
                                      ]),
                                      _: 1
                                    })
                                  ]),
                                  _: 1
                                }))
                              : _createCommentVNode("", true)
                          ]),
                          _: 1
                        })
                      ]),
                      _: 1
                    }))
                  : _createCommentVNode("", true)
              ]),
              _: 1
            }, 8, ["class"])
          ]),
          _: 1
        })
      ]),
      _: 1
    }),
    _createVNode(_component_v_dialog, {
      modelValue: tplDialog.value,
      "onUpdate:modelValue": _cache[22] || (_cache[22] = $event => ((tplDialog).value = $event)),
      "max-width": "760",
      scrollable: ""
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "d-flex align-center flex-wrap ga-2" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  color: "deep-purple",
                  size: "20",
                  class: "mr-1"
                }, {
                  default: _withCtx(() => [...(_cache[80] || (_cache[80] = [
                    _createTextVNode("mdi-cube-outline", -1)
                  ]))]),
                  _: 1
                }),
                _cache[81] || (_cache[81] = _createElementVNode("span", null, "镜像模板", -1)),
                _createVNode(_component_v_chip, {
                  size: "x-small",
                  variant: "tonal",
                  color: "info"
                }, {
                  default: _withCtx(() => [
                    _createTextVNode("ISO " + _toDisplayString(tplCounts.value.iso), 1)
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_chip, {
                  size: "x-small",
                  variant: "tonal",
                  color: "deep-purple"
                }, {
                  default: _withCtx(() => [
                    _createTextVNode("CT 模板 " + _toDisplayString(tplCounts.value.ct), 1)
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  icon: "mdi-refresh",
                  size: "small",
                  variant: "text",
                  loading: tplLoading.value,
                  onClick: fetchTplImages
                }, null, 8, ["loading"]),
                _createVNode(_component_v_btn, {
                  icon: "mdi-close",
                  size: "small",
                  variant: "text",
                  onClick: _cache[21] || (_cache[21] = $event => (tplDialog.value = false))
                })
              ]),
              _: 1
            }),
            _createVNode(_component_v_divider),
            _createVNode(_component_v_card_text, {
              class: "pa-0",
              style: {"max-height":"480px","overflow-y":"auto"}
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_list, {
                  density: "compact",
                  class: "py-0"
                }, {
                  default: _withCtx(() => [
                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(tplList.value, (f) => {
                      return (_openBlock(), _createBlock(_component_v_list_item, {
                        key: f.filenameWithType,
                        class: "px-4"
                      }, {
                        prepend: _withCtx(() => [
                          _createVNode(_component_v_icon, {
                            size: "20",
                            color: f.type === 'iso' ? 'info' : 'deep-purple'
                          }, {
                            default: _withCtx(() => [
                              _createTextVNode(_toDisplayString(f.type === 'iso' ? 'mdi-disc' : 'mdi-cube-outline'), 1)
                            ]),
                            _: 2
                          }, 1032, ["color"])
                        ]),
                        append: _withCtx(() => [
                          _createElementVNode("span", _hoisted_28, [
                            _createTextVNode(_toDisplayString(f.size_mb != null ? f.size_mb.toFixed(2) + ' MB' : '-') + " ", 1),
                            (f.date)
                              ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, [
                                  _createTextVNode(" · " + _toDisplayString(f.date), 1)
                                ], 64))
                              : _createCommentVNode("", true)
                          ])
                        ]),
                        default: _withCtx(() => [
                          _createElementVNode("div", _hoisted_26, [
                            _createElementVNode("span", {
                              class: "text-body-2 text-truncate",
                              title: f.filename
                            }, _toDisplayString(f.filename), 9, _hoisted_27),
                            _createVNode(_component_v_chip, {
                              size: "x-small",
                              color: f.type === 'iso' ? 'info' : 'deep-purple',
                              variant: "tonal"
                            }, {
                              default: _withCtx(() => [
                                _createTextVNode(_toDisplayString(f.type === 'iso' ? 'ISO 镜像' : 'CT 模板'), 1)
                              ]),
                              _: 2
                            }, 1032, ["color"])
                          ])
                        ]),
                        _: 2
                      }, 1024))
                    }), 128)),
                    (!tplList.value.length)
                      ? (_openBlock(), _createBlock(_component_v_list_item, { key: 0 }, {
                          default: _withCtx(() => [
                            _createVNode(_component_v_list_item_title, { class: "text-caption text-medium-emphasis text-center py-4" }, {
                              default: _withCtx(() => [
                                _createTextVNode(_toDisplayString(tplLoading.value ? '加载中...' : '暂无 ISO 镜像 / CT 模板'), 1)
                              ]),
                              _: 1
                            })
                          ]),
                          _: 1
                        }))
                      : _createCommentVNode("", true)
                  ]),
                  _: 1
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"]),
    _createVNode(_component_v_dialog, {
      modelValue: screenDialog.show,
      "onUpdate:modelValue": _cache[29] || (_cache[29] = $event => ((screenDialog.show) = $event)),
      "max-width": "960",
      onAfterLeave: _cache[30] || (_cache[30] = $event => (stopScreenTimer()))
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "d-flex align-center flex-wrap ga-2 py-3" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  color: "deep-purple",
                  size: "20"
                }, {
                  default: _withCtx(() => [...(_cache[82] || (_cache[82] = [
                    _createTextVNode("mdi-monitor-shimmer", -1)
                  ]))]),
                  _: 1
                }),
                _createElementVNode("span", _hoisted_29, "实时画面 · " + _toDisplayString(screenDialog.name) + " (#" + _toDisplayString(screenDialog.vmid) + ")", 1),
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_select, {
                  modelValue: screenRate.value,
                  "onUpdate:modelValue": _cache[23] || (_cache[23] = $event => ((screenRate).value = $event)),
                  items: [
            { title: '1 秒', value: 1 }, { title: '2 秒', value: 2 }, { title: '3 秒', value: 3 },
            { title: '5 秒', value: 5 }, { title: '暂停', value: 0 }],
                  density: "compact",
                  variant: "outlined",
                  "hide-details": "",
                  label: "刷新",
                  style: {"max-width":"110px"}
                }, null, 8, ["modelValue"]),
                _createVNode(_component_v_btn, {
                  size: "small",
                  variant: "text",
                  color: "grey",
                  icon: "mdi-refresh",
                  title: "立即刷新",
                  onClick: _cache[24] || (_cache[24] = $event => (screenTick.value++))
                }),
                _createVNode(_component_v_btn, {
                  size: "small",
                  variant: "tonal",
                  color: "info",
                  "prepend-icon": "mdi-console",
                  title: "完整图形控制台（需登录 PVE）",
                  onClick: _cache[25] || (_cache[25] = $event => (openNovnc({ vmid: screenDialog.vmid, type: 'qemu', displayName: screenDialog.name })))
                }, {
                  default: _withCtx(() => [...(_cache[83] || (_cache[83] = [
                    _createTextVNode(" noVNC ", -1)
                  ]))]),
                  _: 1
                }),
                _createVNode(_component_v_btn, {
                  size: "small",
                  variant: "text",
                  color: "grey",
                  icon: "mdi-close",
                  onClick: _cache[26] || (_cache[26] = $event => (screenDialog.show = false))
                })
              ]),
              _: 1
            }),
            _createVNode(_component_v_divider),
            _createVNode(_component_v_card_text, { class: "pa-0" }, {
              default: _withCtx(() => [
                _createElementVNode("div", _hoisted_30, [
                  (screenError.value)
                    ? (_openBlock(), _createElementBlock("div", _hoisted_31, " 获取画面失败：虚机可能未运行，或显示设备不支持截图。可稍后重试或使用 noVNC 完整控制台。 "))
                    : _createCommentVNode("", true),
                  (screenSrc.value)
                    ? (_openBlock(), _createElementBlock("img", {
                        key: 1,
                        src: screenSrc.value,
                        class: "screen-img",
                        alt: "虚机画面",
                        onError: _cache[27] || (_cache[27] = $event => (screenError.value = true)),
                        onLoad: _cache[28] || (_cache[28] = $event => (screenError.value = false))
                      }, null, 40, _hoisted_32))
                    : _createCommentVNode("", true)
                ]),
                _createVNode(_component_v_alert, {
                  type: "info",
                  variant: "tonal",
                  density: "compact",
                  class: "ma-2 text-caption"
                }, {
                  default: _withCtx(() => [...(_cache[84] || (_cache[84] = [
                    _createTextVNode(" 实时画面为只读监视（每 1~5 秒截图，无需登录 PVE）；需要键鼠操作请点上方「noVNC」打开完整控制台，或在「主机概况 → 宿主机终端」用命令操作。 ", -1)
                  ]))]),
                  _: 1
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"]),
    _createVNode(_component_v_dialog, {
      modelValue: termDialog.value,
      "onUpdate:modelValue": _cache[38] || (_cache[38] = $event => ((termDialog).value = $event)),
      "max-width": "860",
      scrollable: "",
      onAfterLeave: _cache[39] || (_cache[39] = $event => (termOutput.value = ''))
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, { class: "terminal-card" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "d-flex align-center ga-2 py-3" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  color: "deep-purple",
                  size: "20"
                }, {
                  default: _withCtx(() => [...(_cache[85] || (_cache[85] = [
                    _createTextVNode("mdi-console", -1)
                  ]))]),
                  _: 1
                }),
                _createElementVNode("span", _hoisted_33, "宿主机终端 · root@" + _toDisplayString(host.value.hostname || monitorData.value?.node || 'PVE'), 1),
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  size: "small",
                  variant: "text",
                  color: "grey",
                  icon: "mdi-delete-outline",
                  title: "清屏",
                  onClick: _cache[31] || (_cache[31] = $event => (termOutput.value = ''))
                }),
                _createVNode(_component_v_btn, {
                  size: "small",
                  variant: "text",
                  color: "grey",
                  icon: "mdi-close",
                  onClick: _cache[32] || (_cache[32] = $event => (termDialog.value = false))
                })
              ]),
              _: 1
            }),
            _createVNode(_component_v_divider),
            _createVNode(_component_v_card_text, { class: "pa-0" }, {
              default: _withCtx(() => [
                _createElementVNode("div", {
                  ref_key: "termBox",
                  ref: termBox,
                  class: "terminal-box"
                }, [
                  (!termOutput.value)
                    ? (_openBlock(), _createElementBlock("div", _hoisted_34, " 输入命令回车执行（非交互模式，单次超时 20 秒；不支持 top/vim 等全屏程序，请用 top -bn1 等） "))
                    : (_openBlock(), _createElementBlock("pre", _hoisted_35, _toDisplayString(termOutput.value), 1)),
                  (termBusy.value)
                    ? (_openBlock(), _createElementBlock("div", _hoisted_36, [
                        _createVNode(_component_v_icon, {
                          size: "14",
                          class: "mr-1"
                        }, {
                          default: _withCtx(() => [...(_cache[86] || (_cache[86] = [
                            _createTextVNode("mdi-progress-clock", -1)
                          ]))]),
                          _: 1
                        }),
                        _cache[87] || (_cache[87] = _createTextVNode("执行中... ", -1))
                      ]))
                    : _createCommentVNode("", true)
                ], 512),
                _createElementVNode("div", _hoisted_37, [
                  (_openBlock(), _createElementBlock(_Fragment, null, _renderList(quickCmds, (c) => {
                    return _createVNode(_component_v_chip, {
                      key: c,
                      size: "x-small",
                      variant: "tonal",
                      color: "deep-purple",
                      style: {"cursor":"pointer"},
                      onClick: $event => (runCommand(c))
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode(_toDisplayString(c), 1)
                      ]),
                      _: 2
                    }, 1032, ["onClick"])
                  }), 64))
                ])
              ]),
              _: 1
            }),
            _createVNode(_component_v_divider),
            _createVNode(_component_v_card_text, { class: "py-2" }, {
              default: _withCtx(() => [
                _createElementVNode("div", _hoisted_38, [
                  _cache[89] || (_cache[89] = _createElementVNode("span", { class: "terminal-prompt" }, "$", -1)),
                  _createVNode(_component_v_text_field, {
                    modelValue: termInput.value,
                    "onUpdate:modelValue": _cache[33] || (_cache[33] = $event => ((termInput).value = $event)),
                    variant: "plain",
                    density: "compact",
                    "hide-details": "",
                    placeholder: "输入命令，回车执行",
                    style: {"font-family":"monospace"},
                    disabled: termBusy.value,
                    onKeyup: [
                      _cache[34] || (_cache[34] = _withKeys($event => (runCommand()), ["enter"])),
                      _cache[35] || (_cache[35] = _withKeys($event => (termHistoryNav(-1)), ["up"])),
                      _cache[36] || (_cache[36] = _withKeys($event => (termHistoryNav(1)), ["down"]))
                    ]
                  }, null, 8, ["modelValue", "disabled"]),
                  _createVNode(_component_v_btn, {
                    color: "deep-purple",
                    variant: "tonal",
                    size: "small",
                    loading: termBusy.value,
                    onClick: _cache[37] || (_cache[37] = $event => (runCommand()))
                  }, {
                    default: _withCtx(() => [...(_cache[88] || (_cache[88] = [
                      _createTextVNode(" 执行 ", -1)
                    ]))]),
                    _: 1
                  }, 8, ["loading"])
                ])
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"]),
    _createVNode(_component_v_dialog, {
      modelValue: guestDialog.show,
      "onUpdate:modelValue": _cache[42] || (_cache[42] = $event => ((guestDialog.show) = $event)),
      "max-width": "760",
      scrollable: ""
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "d-flex align-center flex-wrap ga-2" }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  color: "primary",
                  size: "20",
                  class: "mr-1"
                }, {
                  default: _withCtx(() => [...(_cache[90] || (_cache[90] = [
                    _createTextVNode("mdi-chart-line", -1)
                  ]))]),
                  _: 1
                }),
                _createElementVNode("span", null, _toDisplayString(guestDialog.name), 1),
                _createElementVNode("span", _hoisted_39, "#" + _toDisplayString(guestDialog.vmid) + " · " + _toDisplayString(guestDialog.type === 'lxc' ? 'LXC' : 'VM'), 1),
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn_toggle, {
                  modelValue: guestTf.value,
                  "onUpdate:modelValue": _cache[40] || (_cache[40] = $event => ((guestTf).value = $event)),
                  mandatory: "",
                  density: "compact",
                  variant: "outlined",
                  divided: ""
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_btn, {
                      value: "hour",
                      size: "small"
                    }, {
                      default: _withCtx(() => [...(_cache[91] || (_cache[91] = [
                        _createTextVNode("小时", -1)
                      ]))]),
                      _: 1
                    }),
                    _createVNode(_component_v_btn, {
                      value: "day",
                      size: "small"
                    }, {
                      default: _withCtx(() => [...(_cache[92] || (_cache[92] = [
                        _createTextVNode("天", -1)
                      ]))]),
                      _: 1
                    }),
                    _createVNode(_component_v_btn, {
                      value: "week",
                      size: "small"
                    }, {
                      default: _withCtx(() => [...(_cache[93] || (_cache[93] = [
                        _createTextVNode("周", -1)
                      ]))]),
                      _: 1
                    }),
                    _createVNode(_component_v_btn, {
                      value: "month",
                      size: "small"
                    }, {
                      default: _withCtx(() => [...(_cache[94] || (_cache[94] = [
                        _createTextVNode("月", -1)
                      ]))]),
                      _: 1
                    })
                  ]),
                  _: 1
                }, 8, ["modelValue"]),
                _createVNode(_component_v_btn, {
                  icon: "mdi-close",
                  size: "small",
                  variant: "text",
                  onClick: _cache[41] || (_cache[41] = $event => (guestDialog.show = false))
                })
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                (guestCharts.value.length)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_40, [
                      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(guestCharts.value, (ch) => {
                        return (_openBlock(), _createElementBlock("div", {
                          key: ch.key,
                          class: "chart-cell"
                        }, [
                          _createElementVNode("div", _hoisted_41, [
                            _createElementVNode("span", null, _toDisplayString(ch.title), 1),
                            _createElementVNode("span", {
                              class: "font-weight-bold",
                              style: _normalizeStyle({ color: ch.lines.length > 1 ? '' : ch.lines[0].color })
                            }, _toDisplayString(ch.last), 5)
                          ]),
                          (_openBlock(), _createElementBlock("svg", _hoisted_42, [
                            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(ch.lines, (ln, i) => {
                              return (_openBlock(), _createElementBlock(_Fragment, { key: i }, [
                                _createElementVNode("polygon", {
                                  points: ln.areaPoints,
                                  fill: ln.color,
                                  opacity: "0.12",
                                  stroke: "none"
                                }, null, 8, _hoisted_43),
                                _createElementVNode("polyline", {
                                  points: ln.points,
                                  fill: "none",
                                  stroke: ln.color,
                                  "stroke-width": "1.6"
                                }, null, 8, _hoisted_44)
                              ], 64))
                            }), 128))
                          ]))
                        ]))
                      }), 128))
                    ]))
                  : (_openBlock(), _createElementBlock("div", _hoisted_45, _toDisplayString(guestLoading.value ? '加载中...' : '暂无监控数据'), 1))
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"]),
    _createVNode(_component_v_dialog, {
      modelValue: restoreDialog.show,
      "onUpdate:modelValue": _cache[45] || (_cache[45] = $event => ((restoreDialog.show) = $event)),
      "max-width": "420"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "text-subtitle-1" }, {
              default: _withCtx(() => [...(_cache[95] || (_cache[95] = [
                _createTextVNode("恢复备份", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                _createElementVNode("div", {
                  class: "text-body-2 mb-3 text-truncate",
                  title: restoreDialog.item?.filename
                }, [
                  _createTextVNode(_toDisplayString(restoreDialog.item?.filename) + " ", 1),
                  _createElementVNode("span", _hoisted_47, "（" + _toDisplayString(restoreDialog.item?.source) + "）", 1)
                ], 8, _hoisted_46),
                _createVNode(_component_v_text_field, {
                  modelValue: restoreDialog.vmid,
                  "onUpdate:modelValue": _cache[43] || (_cache[43] = $event => ((restoreDialog.vmid) = $event)),
                  label: "目标 VMID（可选，默认恢复到原机）",
                  density: "compact",
                  variant: "outlined",
                  "hide-details": ""
                }, null, 8, ["modelValue"])
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  variant: "text",
                  onClick: _cache[44] || (_cache[44] = $event => (restoreDialog.show = false))
                }, {
                  default: _withCtx(() => [...(_cache[96] || (_cache[96] = [
                    _createTextVNode("取消", -1)
                  ]))]),
                  _: 1
                }),
                _createVNode(_component_v_btn, {
                  color: "deep-purple",
                  variant: "tonal",
                  loading: busy.restore,
                  onClick: doRestore
                }, {
                  default: _withCtx(() => [...(_cache[97] || (_cache[97] = [
                    _createTextVNode("开始恢复", -1)
                  ]))]),
                  _: 1
                }, 8, ["loading"])
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"]),
    _createVNode(_component_v_dialog, {
      modelValue: confirmDialog.show,
      "onUpdate:modelValue": _cache[48] || (_cache[48] = $event => ((confirmDialog.show) = $event)),
      "max-width": "380"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, { class: "text-subtitle-1" }, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(confirmDialog.title), 1)
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_text, { class: "text-body-2" }, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(confirmDialog.text), 1)
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  variant: "text",
                  onClick: _cache[46] || (_cache[46] = $event => (confirmDialog.show = false))
                }, {
                  default: _withCtx(() => [...(_cache[98] || (_cache[98] = [
                    _createTextVNode("取消", -1)
                  ]))]),
                  _: 1
                }),
                _createVNode(_component_v_btn, {
                  color: "error",
                  variant: "tonal",
                  onClick: _cache[47] || (_cache[47] = $event => (confirmDialog.confirm && confirmDialog.confirm()))
                }, {
                  default: _withCtx(() => [...(_cache[99] || (_cache[99] = [
                    _createTextVNode("确认执行", -1)
                  ]))]),
                  _: 1
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }, 8, ["modelValue"]),
    _createVNode(_component_v_snackbar, {
      modelValue: snackbar.value.show,
      "onUpdate:modelValue": _cache[49] || (_cache[49] = $event => ((snackbar.value.show) = $event)),
      color: snackbar.value.color,
      timeout: "3000"
    }, {
      default: _withCtx(() => [
        _createTextVNode(_toDisplayString(snackbar.value.text), 1)
      ]),
      _: 1
    }, 8, ["modelValue", "color"])
  ]))
}
}

};
const AppPage = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-ecb8b42c"]]);

export { AppPage as default };
