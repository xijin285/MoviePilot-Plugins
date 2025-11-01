import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { c as commonjsGlobal, g as getDefaultExportFromCjs, a as cronstrue } from './zh_CN-CNefNtEK.js';
import { _ as _export_sfc } from './_plugin-vue_export-helper-pcqpp-6-.js';

function bind(fn, thisArg) {
  return function wrap() {
    return fn.apply(thisArg, arguments);
  };
}

// utils is a library of generic helper functions non-specific to axios

const {toString} = Object.prototype;
const {getPrototypeOf} = Object;
const {iterator, toStringTag} = Symbol;

const kindOf = (cache => thing => {
    const str = toString.call(thing);
    return cache[str] || (cache[str] = str.slice(8, -1).toLowerCase());
})(Object.create(null));

const kindOfTest = (type) => {
  type = type.toLowerCase();
  return (thing) => kindOf(thing) === type
};

const typeOfTest = type => thing => typeof thing === type;

/**
 * Determine if a value is an Array
 *
 * @param {Object} val The value to test
 *
 * @returns {boolean} True if value is an Array, otherwise false
 */
const {isArray} = Array;

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
  return val !== null && !isUndefined(val) && val.constructor !== null && !isUndefined(val.constructor)
    && isFunction(val.constructor.isBuffer) && val.constructor.isBuffer(val);
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
  if ((typeof ArrayBuffer !== 'undefined') && (ArrayBuffer.isView)) {
    result = ArrayBuffer.isView(val);
  } else {
    result = (val) && (val.buffer) && (isArrayBuffer(val.buffer));
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
const isFunction = typeOfTest('function');

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
const isBoolean = thing => thing === true || thing === false;

/**
 * Determine if a value is a plain Object
 *
 * @param {*} val The value to test
 *
 * @returns {boolean} True if value is a plain Object, otherwise false
 */
const isPlainObject = (val) => {
  if (kindOf(val) !== 'object') {
    return false;
  }

  const prototype = getPrototypeOf(val);
  return (prototype === null || prototype === Object.prototype || Object.getPrototypeOf(prototype) === null) && !(toStringTag in val) && !(iterator in val);
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
 * @returns {boolean} True if value is a File, otherwise false
 */
const isFileList = kindOfTest('FileList');

/**
 * Determine if a value is a Stream
 *
 * @param {*} val The value to test
 *
 * @returns {boolean} True if value is a Stream, otherwise false
 */
const isStream = (val) => isObject(val) && isFunction(val.pipe);

/**
 * Determine if a value is a FormData
 *
 * @param {*} thing The value to test
 *
 * @returns {boolean} True if value is an FormData, otherwise false
 */
const isFormData = (thing) => {
  let kind;
  return thing && (
    (typeof FormData === 'function' && thing instanceof FormData) || (
      isFunction(thing.append) && (
        (kind = kindOf(thing)) === 'formdata' ||
        // detect form-data instance
        (kind === 'object' && isFunction(thing.toString) && thing.toString() === '[object FormData]')
      )
    )
  )
};

/**
 * Determine if a value is a URLSearchParams object
 *
 * @param {*} val The value to test
 *
 * @returns {boolean} True if value is a URLSearchParams object, otherwise false
 */
const isURLSearchParams = kindOfTest('URLSearchParams');

const [isReadableStream, isRequest, isResponse, isHeaders] = ['ReadableStream', 'Request', 'Response', 'Headers'].map(kindOfTest);

/**
 * Trim excess whitespace off the beginning and end of a string
 *
 * @param {String} str The String to trim
 *
 * @returns {String} The String freed of excess whitespace
 */
const trim = (str) => str.trim ?
  str.trim() : str.replace(/^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g, '');

/**
 * Iterate over an Array or an Object invoking a function for each item.
 *
 * If `obj` is an Array callback will be called passing
 * the value, index, and complete array for each item.
 *
 * If 'obj' is an Object callback will be called passing
 * the value, key, and complete object for each property.
 *
 * @param {Object|Array} obj The object to iterate
 * @param {Function} fn The callback to invoke for each item
 *
 * @param {Boolean} [allOwnKeys = false]
 * @returns {any}
 */
function forEach(obj, fn, {allOwnKeys = false} = {}) {
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

function findKey(obj, key) {
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
  if (typeof globalThis !== "undefined") return globalThis;
  return typeof self !== "undefined" ? self : (typeof window !== 'undefined' ? window : global)
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
 * var result = merge({foo: 123}, {foo: 456});
 * console.log(result.foo); // outputs 456
 * ```
 *
 * @param {Object} obj1 Object to merge
 *
 * @returns {Object} Result of all merge properties
 */
function merge(/* obj1, obj2, obj3, ... */) {
  const {caseless} = isContextDefined(this) && this || {};
  const result = {};
  const assignValue = (val, key) => {
    const targetKey = caseless && findKey(result, key) || key;
    if (isPlainObject(result[targetKey]) && isPlainObject(val)) {
      result[targetKey] = merge(result[targetKey], val);
    } else if (isPlainObject(val)) {
      result[targetKey] = merge({}, val);
    } else if (isArray(val)) {
      result[targetKey] = val.slice();
    } else {
      result[targetKey] = val;
    }
  };

  for (let i = 0, l = arguments.length; i < l; i++) {
    arguments[i] && forEach(arguments[i], assignValue);
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
 * @param {Boolean} [allOwnKeys]
 * @returns {Object} The resulting value of object a
 */
const extend = (a, b, thisArg, {allOwnKeys}= {}) => {
  forEach(b, (val, key) => {
    if (thisArg && isFunction(val)) {
      a[key] = bind(val, thisArg);
    } else {
      a[key] = val;
    }
  }, {allOwnKeys});
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
  if (content.charCodeAt(0) === 0xFEFF) {
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
  constructor.prototype.constructor = constructor;
  Object.defineProperty(constructor, 'super', {
    value: superConstructor.prototype
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
  if (!isNumber(i)) return null;
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
const isTypedArray = (TypedArray => {
  // eslint-disable-next-line func-names
  return thing => {
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

const toCamelCase = str => {
  return str.toLowerCase().replace(/[-_\s]([a-z\d])(\w*)/g,
    function replacer(m, p1, p2) {
      return p1.toUpperCase() + p2;
    }
  );
};

/* Creating a function that will check if an object has a property. */
const hasOwnProperty = (({hasOwnProperty}) => (obj, prop) => hasOwnProperty.call(obj, prop))(Object.prototype);

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
    if (isFunction(obj) && ['arguments', 'caller', 'callee'].indexOf(name) !== -1) {
      return false;
    }

    const value = obj[name];

    if (!isFunction(value)) return;

    descriptor.enumerable = false;

    if ('writable' in descriptor) {
      descriptor.writable = false;
      return;
    }

    if (!descriptor.set) {
      descriptor.set = () => {
        throw Error('Can not rewrite read-only method \'' + name + '\'');
      };
    }
  });
};

const toObjectSet = (arrayOrString, delimiter) => {
  const obj = {};

  const define = (arr) => {
    arr.forEach(value => {
      obj[value] = true;
    });
  };

  isArray(arrayOrString) ? define(arrayOrString) : define(String(arrayOrString).split(delimiter));

  return obj;
};

const noop = () => {};

const toFiniteNumber = (value, defaultValue) => {
  return value != null && Number.isFinite(value = +value) ? value : defaultValue;
};

/**
 * If the thing is a FormData object, return true, otherwise return false.
 *
 * @param {unknown} thing - The thing to check.
 *
 * @returns {boolean}
 */
function isSpecCompliantForm(thing) {
  return !!(thing && isFunction(thing.append) && thing[toStringTag] === 'FormData' && thing[iterator]);
}

const toJSONObject = (obj) => {
  const stack = new Array(10);

  const visit = (source, i) => {

    if (isObject(source)) {
      if (stack.indexOf(source) >= 0) {
        return;
      }

      if(!('toJSON' in source)) {
        stack[i] = source;
        const target = isArray(source) ? [] : {};

        forEach(source, (value, key) => {
          const reducedValue = visit(value, i + 1);
          !isUndefined(reducedValue) && (target[key] = reducedValue);
        });

        stack[i] = undefined;

        return target;
      }
    }

    return source;
  };

  return visit(obj, 0);
};

const isAsyncFn = kindOfTest('AsyncFunction');

const isThenable = (thing) =>
  thing && (isObject(thing) || isFunction(thing)) && isFunction(thing.then) && isFunction(thing.catch);

// original code
// https://github.com/DigitalBrainJS/AxiosPromise/blob/16deab13710ec09779922131f3fa5954320f83ab/lib/utils.js#L11-L34

const _setImmediate = ((setImmediateSupported, postMessageSupported) => {
  if (setImmediateSupported) {
    return setImmediate;
  }

  return postMessageSupported ? ((token, callbacks) => {
    _global.addEventListener("message", ({source, data}) => {
      if (source === _global && data === token) {
        callbacks.length && callbacks.shift()();
      }
    }, false);

    return (cb) => {
      callbacks.push(cb);
      _global.postMessage(token, "*");
    }
  })(`axios@${Math.random()}`, []) : (cb) => setTimeout(cb);
})(
  typeof setImmediate === 'function',
  isFunction(_global.postMessage)
);

const asap = typeof queueMicrotask !== 'undefined' ?
  queueMicrotask.bind(_global) : ( typeof process !== 'undefined' && process.nextTick || _setImmediate);

// *********************


const isIterable = (thing) => thing != null && isFunction(thing[iterator]);


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
  isReadableStream,
  isRequest,
  isResponse,
  isHeaders,
  isUndefined,
  isDate,
  isFile,
  isBlob,
  isRegExp,
  isFunction,
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
  isIterable
};

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
function AxiosError$1(message, code, config, request, response) {
  Error.call(this);

  if (Error.captureStackTrace) {
    Error.captureStackTrace(this, this.constructor);
  } else {
    this.stack = (new Error()).stack;
  }

  this.message = message;
  this.name = 'AxiosError';
  code && (this.code = code);
  config && (this.config = config);
  request && (this.request = request);
  if (response) {
    this.response = response;
    this.status = response.status ? response.status : null;
  }
}

utils$1.inherits(AxiosError$1, Error, {
  toJSON: function toJSON() {
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
      config: utils$1.toJSONObject(this.config),
      code: this.code,
      status: this.status
    };
  }
});

const prototype$1 = AxiosError$1.prototype;
const descriptors = {};

[
  'ERR_BAD_OPTION_VALUE',
  'ERR_BAD_OPTION',
  'ECONNABORTED',
  'ETIMEDOUT',
  'ERR_NETWORK',
  'ERR_FR_TOO_MANY_REDIRECTS',
  'ERR_DEPRECATED',
  'ERR_BAD_RESPONSE',
  'ERR_BAD_REQUEST',
  'ERR_CANCELED',
  'ERR_NOT_SUPPORT',
  'ERR_INVALID_URL'
// eslint-disable-next-line func-names
].forEach(code => {
  descriptors[code] = {value: code};
});

Object.defineProperties(AxiosError$1, descriptors);
Object.defineProperty(prototype$1, 'isAxiosError', {value: true});

// eslint-disable-next-line func-names
AxiosError$1.from = (error, code, config, request, response, customProps) => {
  const axiosError = Object.create(prototype$1);

  utils$1.toFlatObject(error, axiosError, function filter(obj) {
    return obj !== Error.prototype;
  }, prop => {
    return prop !== 'isAxiosError';
  });

  AxiosError$1.call(axiosError, error.message, code, config, request, response);

  axiosError.cause = error;

  axiosError.name = error.name;

  customProps && Object.assign(axiosError, customProps);

  return axiosError;
};

// eslint-disable-next-line strict
const httpAdapter = null;

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
  return path.concat(key).map(function each(token, i) {
    // eslint-disable-next-line no-param-reassign
    token = removeBrackets(token);
    return !dots && i ? '[' + token + ']' : token;
  }).join(dots ? '.' : '');
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
function toFormData$1(obj, formData, options) {
  if (!utils$1.isObject(obj)) {
    throw new TypeError('target must be an object');
  }

  // eslint-disable-next-line no-param-reassign
  formData = formData || new (FormData)();

  // eslint-disable-next-line no-param-reassign
  options = utils$1.toFlatObject(options, {
    metaTokens: true,
    dots: false,
    indexes: false
  }, false, function defined(option, source) {
    // eslint-disable-next-line no-eq-null,eqeqeq
    return !utils$1.isUndefined(source[option]);
  });

  const metaTokens = options.metaTokens;
  // eslint-disable-next-line no-use-before-define
  const visitor = options.visitor || defaultVisitor;
  const dots = options.dots;
  const indexes = options.indexes;
  const _Blob = options.Blob || typeof Blob !== 'undefined' && Blob;
  const useBlob = _Blob && utils$1.isSpecCompliantForm(formData);

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
      return useBlob && typeof Blob === 'function' ? new Blob([value]) : Buffer.from(value);
    }

    return value;
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

    if (value && !path && typeof value === 'object') {
      if (utils$1.endsWith(key, '{}')) {
        // eslint-disable-next-line no-param-reassign
        key = metaTokens ? key : key.slice(0, -2);
        // eslint-disable-next-line no-param-reassign
        value = JSON.stringify(value);
      } else if (
        (utils$1.isArray(value) && isFlatArray(value)) ||
        ((utils$1.isFileList(value) || utils$1.endsWith(key, '[]')) && (arr = utils$1.toArray(value))
        )) {
        // eslint-disable-next-line no-param-reassign
        key = removeBrackets(key);

        arr.forEach(function each(el, index) {
          !(utils$1.isUndefined(el) || el === null) && formData.append(
            // eslint-disable-next-line no-nested-ternary
            indexes === true ? renderKey([key], index, dots) : (indexes === null ? key : key + '[]'),
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

  const stack = [];

  const exposedHelpers = Object.assign(predicates, {
    defaultVisitor,
    convertValue,
    isVisitable
  });

  function build(value, path) {
    if (utils$1.isUndefined(value)) return;

    if (stack.indexOf(value) !== -1) {
      throw Error('Circular reference detected in ' + path.join('.'));
    }

    stack.push(value);

    utils$1.forEach(value, function each(el, key) {
      const result = !(utils$1.isUndefined(el) || el === null) && visitor.call(
        formData, el, utils$1.isString(key) ? key.trim() : key, path, exposedHelpers
      );

      if (result === true) {
        build(el, path ? path.concat(key) : [key]);
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
    '%00': '\x00'
  };
  return encodeURIComponent(str).replace(/[!'()~]|%20|%00/g, function replacer(match) {
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

  params && toFormData$1(params, this, options);
}

const prototype = AxiosURLSearchParams.prototype;

prototype.append = function append(name, value) {
  this._pairs.push([name, value]);
};

prototype.toString = function toString(encoder) {
  const _encode = encoder ? function(value) {
    return encoder.call(this, value, encode$1);
  } : encode$1;

  return this._pairs.map(function each(pair) {
    return _encode(pair[0]) + '=' + _encode(pair[1]);
  }, '').join('&');
};

/**
 * It replaces all instances of the characters `:`, `$`, `,`, `+`, `[`, and `]` with their
 * URI encoded counterparts
 *
 * @param {string} val The value to be encoded.
 *
 * @returns {string} The encoded value.
 */
function encode(val) {
  return encodeURIComponent(val).
    replace(/%3A/gi, ':').
    replace(/%24/g, '$').
    replace(/%2C/gi, ',').
    replace(/%20/g, '+').
    replace(/%5B/gi, '[').
    replace(/%5D/gi, ']');
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
  /*eslint no-param-reassign:0*/
  if (!params) {
    return url;
  }
  
  const _encode = options && options.encode || encode;

  if (utils$1.isFunction(options)) {
    options = {
      serialize: options
    };
  } 

  const serializeFn = options && options.serialize;

  let serializedParams;

  if (serializeFn) {
    serializedParams = serializeFn(params, options);
  } else {
    serializedParams = utils$1.isURLSearchParams(params) ?
      params.toString() :
      new AxiosURLSearchParams(params, options).toString(_encode);
  }

  if (serializedParams) {
    const hashmarkIndex = url.indexOf("#");

    if (hashmarkIndex !== -1) {
      url = url.slice(0, hashmarkIndex);
    }
    url += (url.indexOf('?') === -1 ? '?' : '&') + serializedParams;
  }

  return url;
}

class InterceptorManager {
  constructor() {
    this.handlers = [];
  }

  /**
   * Add a new interceptor to the stack
   *
   * @param {Function} fulfilled The function to handle `then` for a `Promise`
   * @param {Function} rejected The function to handle `reject` for a `Promise`
   *
   * @return {Number} An ID used to remove interceptor later
   */
  use(fulfilled, rejected, options) {
    this.handlers.push({
      fulfilled,
      rejected,
      synchronous: options ? options.synchronous : false,
      runWhen: options ? options.runWhen : null
    });
    return this.handlers.length - 1;
  }

  /**
   * Remove an interceptor from the stack
   *
   * @param {Number} id The ID that was returned by `use`
   *
   * @returns {Boolean} `true` if the interceptor was removed, `false` otherwise
   */
  eject(id) {
    if (this.handlers[id]) {
      this.handlers[id] = null;
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
    utils$1.forEach(this.handlers, function forEachHandler(h) {
      if (h !== null) {
        fn(h);
      }
    });
  }
}

const transitionalDefaults = {
  silentJSONParsing: true,
  forcedJSONParsing: true,
  clarifyTimeoutError: false
};

const URLSearchParams$1 = typeof URLSearchParams !== 'undefined' ? URLSearchParams : AxiosURLSearchParams;

const FormData$1 = typeof FormData !== 'undefined' ? FormData : null;

const Blob$1 = typeof Blob !== 'undefined' ? Blob : null;

const platform$1 = {
  isBrowser: true,
  classes: {
    URLSearchParams: URLSearchParams$1,
    FormData: FormData$1,
    Blob: Blob$1
  },
  protocols: ['http', 'https', 'file', 'blob', 'url', 'data']
};

const hasBrowserEnv = typeof window !== 'undefined' && typeof document !== 'undefined';

const _navigator = typeof navigator === 'object' && navigator || undefined;

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
const hasStandardBrowserEnv = hasBrowserEnv &&
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

const origin = hasBrowserEnv && window.location.href || 'http://localhost';

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
  ...platform$1
};

function toURLEncodedForm(data, options) {
  return toFormData$1(data, new platform.classes.URLSearchParams(), Object.assign({
    visitor: function(value, key, path, helpers) {
      if (platform.isNode && utils$1.isBuffer(value)) {
        this.append(key, value.toString('base64'));
        return false;
      }

      return helpers.defaultVisitor.apply(this, arguments);
    }
  }, options));
}

/**
 * It takes a string like `foo[x][y][z]` and returns an array like `['foo', 'x', 'y', 'z']
 *
 * @param {string} name - The name of the property to get.
 *
 * @returns An array of strings.
 */
function parsePropPath(name) {
  // foo[x][y][z]
  // foo.x.y.z
  // foo-x-y-z
  // foo x y z
  return utils$1.matchAll(/\w+|\[(\w*)]/g, name).map(match => {
    return match[0] === '[]' ? '' : match[1] || match[0];
  });
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

/**
 * It takes a FormData object and returns a JavaScript object
 *
 * @param {string} formData The FormData object to convert to JSON.
 *
 * @returns {Object<string, any> | null} The converted object.
 */
function formDataToJSON(formData) {
  function buildPath(path, value, target, index) {
    let name = path[index++];

    if (name === '__proto__') return true;

    const isNumericKey = Number.isFinite(+name);
    const isLast = index >= path.length;
    name = !name && utils$1.isArray(target) ? target.length : name;

    if (isLast) {
      if (utils$1.hasOwnProp(target, name)) {
        target[name] = [target[name], value];
      } else {
        target[name] = value;
      }

      return !isNumericKey;
    }

    if (!target[name] || !utils$1.isObject(target[name])) {
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

    return obj;
  }

  return null;
}

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

  transformRequest: [function transformRequest(data, headers) {
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

    if (utils$1.isArrayBuffer(data) ||
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
      if (contentType.indexOf('application/x-www-form-urlencoded') > -1) {
        return toURLEncodedForm(data, this.formSerializer).toString();
      }

      if ((isFileList = utils$1.isFileList(data)) || contentType.indexOf('multipart/form-data') > -1) {
        const _FormData = this.env && this.env.FormData;

        return toFormData$1(
          isFileList ? {'files[]': data} : data,
          _FormData && new _FormData(),
          this.formSerializer
        );
      }
    }

    if (isObjectPayload || hasJSONContentType ) {
      headers.setContentType('application/json', false);
      return stringifySafely(data);
    }

    return data;
  }],

  transformResponse: [function transformResponse(data) {
    const transitional = this.transitional || defaults.transitional;
    const forcedJSONParsing = transitional && transitional.forcedJSONParsing;
    const JSONRequested = this.responseType === 'json';

    if (utils$1.isResponse(data) || utils$1.isReadableStream(data)) {
      return data;
    }

    if (data && utils$1.isString(data) && ((forcedJSONParsing && !this.responseType) || JSONRequested)) {
      const silentJSONParsing = transitional && transitional.silentJSONParsing;
      const strictJSONParsing = !silentJSONParsing && JSONRequested;

      try {
        return JSON.parse(data);
      } catch (e) {
        if (strictJSONParsing) {
          if (e.name === 'SyntaxError') {
            throw AxiosError$1.from(e, AxiosError$1.ERR_BAD_RESPONSE, this, null, this.response);
          }
          throw e;
        }
      }
    }

    return data;
  }],

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
    Blob: platform.classes.Blob
  },

  validateStatus: function validateStatus(status) {
    return status >= 200 && status < 300;
  },

  headers: {
    common: {
      'Accept': 'application/json, text/plain, */*',
      'Content-Type': undefined
    }
  }
};

utils$1.forEach(['delete', 'get', 'head', 'post', 'put', 'patch'], (method) => {
  defaults.headers[method] = {};
});

// RawAxiosHeaders whose duplicates are ignored by node
// c.f. https://nodejs.org/api/http.html#http_message_headers
const ignoreDuplicateOf = utils$1.toObjectSet([
  'age', 'authorization', 'content-length', 'content-type', 'etag',
  'expires', 'from', 'host', 'if-modified-since', 'if-unmodified-since',
  'last-modified', 'location', 'max-forwards', 'proxy-authorization',
  'referer', 'retry-after', 'user-agent'
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
const parseHeaders = rawHeaders => {
  const parsed = {};
  let key;
  let val;
  let i;

  rawHeaders && rawHeaders.split('\n').forEach(function parser(line) {
    i = line.indexOf(':');
    key = line.substring(0, i).trim().toLowerCase();
    val = line.substring(i + 1).trim();

    if (!key || (parsed[key] && ignoreDuplicateOf[key])) {
      return;
    }

    if (key === 'set-cookie') {
      if (parsed[key]) {
        parsed[key].push(val);
      } else {
        parsed[key] = [val];
      }
    } else {
      parsed[key] = parsed[key] ? parsed[key] + ', ' + val : val;
    }
  });

  return parsed;
};

const $internals = Symbol('internals');

function normalizeHeader(header) {
  return header && String(header).trim().toLowerCase();
}

function normalizeValue(value) {
  if (value === false || value == null) {
    return value;
  }

  return utils$1.isArray(value) ? value.map(normalizeValue) : String(value);
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

const isValidHeaderName = (str) => /^[-_a-zA-Z0-9^`|~,!#$%&'*+.]+$/.test(str.trim());

function matchHeaderValue(context, value, header, filter, isHeaderNameFilter) {
  if (utils$1.isFunction(filter)) {
    return filter.call(this, value, header);
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
  return header.trim()
    .toLowerCase().replace(/([a-z\d])(\w*)/g, (w, char, str) => {
      return char.toUpperCase() + str;
    });
}

function buildAccessors(obj, header) {
  const accessorName = utils$1.toCamelCase(' ' + header);

  ['get', 'set', 'has'].forEach(methodName => {
    Object.defineProperty(obj, methodName + accessorName, {
      value: function(arg1, arg2, arg3) {
        return this[methodName].call(this, header, arg1, arg2, arg3);
      },
      configurable: true
    });
  });
}

let AxiosHeaders$1 = class AxiosHeaders {
  constructor(headers) {
    headers && this.set(headers);
  }

  set(header, valueOrRewrite, rewrite) {
    const self = this;

    function setHeader(_value, _header, _rewrite) {
      const lHeader = normalizeHeader(_header);

      if (!lHeader) {
        throw new Error('header name must be a non-empty string');
      }

      const key = utils$1.findKey(self, lHeader);

      if(!key || self[key] === undefined || _rewrite === true || (_rewrite === undefined && self[key] !== false)) {
        self[key || _header] = normalizeValue(_value);
      }
    }

    const setHeaders = (headers, _rewrite) =>
      utils$1.forEach(headers, (_value, _header) => setHeader(_value, _header, _rewrite));

    if (utils$1.isPlainObject(header) || header instanceof this.constructor) {
      setHeaders(header, valueOrRewrite);
    } else if(utils$1.isString(header) && (header = header.trim()) && !isValidHeaderName(header)) {
      setHeaders(parseHeaders(header), valueOrRewrite);
    } else if (utils$1.isObject(header) && utils$1.isIterable(header)) {
      let obj = {}, dest, key;
      for (const entry of header) {
        if (!utils$1.isArray(entry)) {
          throw TypeError('Object iterator must return a key-value pair');
        }

        obj[key = entry[0]] = (dest = obj[key]) ?
          (utils$1.isArray(dest) ? [...dest, entry[1]] : [dest, entry[1]]) : entry[1];
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

      return !!(key && this[key] !== undefined && (!matcher || matchHeaderValue(this, this[key], key, matcher)));
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
      if(!matcher || matchHeaderValue(this, this[key], key, matcher, true)) {
        delete this[key];
        deleted = true;
      }
    }

    return deleted;
  }

  normalize(format) {
    const self = this;
    const headers = {};

    utils$1.forEach(this, (value, header) => {
      const key = utils$1.findKey(headers, header);

      if (key) {
        self[key] = normalizeValue(value);
        delete self[header];
        return;
      }

      const normalized = format ? formatHeader(header) : String(header).trim();

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
      value != null && value !== false && (obj[header] = asStrings && utils$1.isArray(value) ? value.join(', ') : value);
    });

    return obj;
  }

  [Symbol.iterator]() {
    return Object.entries(this.toJSON())[Symbol.iterator]();
  }

  toString() {
    return Object.entries(this.toJSON()).map(([header, value]) => header + ': ' + value).join('\n');
  }

  getSetCookie() {
    return this.get("set-cookie") || [];
  }

  get [Symbol.toStringTag]() {
    return 'AxiosHeaders';
  }

  static from(thing) {
    return thing instanceof this ? thing : new this(thing);
  }

  static concat(first, ...targets) {
    const computed = new this(first);

    targets.forEach((target) => computed.set(target));

    return computed;
  }

  static accessor(header) {
    const internals = this[$internals] = (this[$internals] = {
      accessors: {}
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
};

AxiosHeaders$1.accessor(['Content-Type', 'Content-Length', 'Accept', 'Accept-Encoding', 'User-Agent', 'Authorization']);

// reserved names hotfix
utils$1.reduceDescriptors(AxiosHeaders$1.prototype, ({value}, key) => {
  let mapped = key[0].toUpperCase() + key.slice(1); // map `set` => `Set`
  return {
    get: () => value,
    set(headerValue) {
      this[mapped] = headerValue;
    }
  }
});

utils$1.freezeMethods(AxiosHeaders$1);

/**
 * Transform the data for a request or a response
 *
 * @param {Array|Function} fns A single function or Array of functions
 * @param {?Object} response The response object
 *
 * @returns {*} The resulting transformed data
 */
function transformData(fns, response) {
  const config = this || defaults;
  const context = response || config;
  const headers = AxiosHeaders$1.from(context.headers);
  let data = context.data;

  utils$1.forEach(fns, function transform(fn) {
    data = fn.call(config, data, headers.normalize(), response ? response.status : undefined);
  });

  headers.normalize();

  return data;
}

function isCancel$1(value) {
  return !!(value && value.__CANCEL__);
}

/**
 * A `CanceledError` is an object that is thrown when an operation is canceled.
 *
 * @param {string=} message The message.
 * @param {Object=} config The config.
 * @param {Object=} request The request.
 *
 * @returns {CanceledError} The created error.
 */
function CanceledError$1(message, config, request) {
  // eslint-disable-next-line no-eq-null,eqeqeq
  AxiosError$1.call(this, message == null ? 'canceled' : message, AxiosError$1.ERR_CANCELED, config, request);
  this.name = 'CanceledError';
}

utils$1.inherits(CanceledError$1, AxiosError$1, {
  __CANCEL__: true
});

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
      [AxiosError$1.ERR_BAD_REQUEST, AxiosError$1.ERR_BAD_RESPONSE][Math.floor(response.status / 100) - 4],
      response.config,
      response.request,
      response
    ));
  }
}

function parseProtocol(url) {
  const match = /^([-+\w]{1,25})(:?\/\/|:)/.exec(url);
  return match && match[1] || '';
}

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

    return passed ? Math.round(bytesCount * 1000 / passed) : undefined;
  };
}

/**
 * Throttle decorator
 * @param {Function} fn
 * @param {Number} freq
 * @return {Function}
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
    fn.apply(null, args);
  };

  const throttled = (...args) => {
    const now = Date.now();
    const passed = now - timestamp;
    if ( passed >= threshold) {
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

  return [throttled, flush];
}

const progressEventReducer = (listener, isDownloadStream, freq = 3) => {
  let bytesNotified = 0;
  const _speedometer = speedometer(50, 250);

  return throttle(e => {
    const loaded = e.loaded;
    const total = e.lengthComputable ? e.total : undefined;
    const progressBytes = loaded - bytesNotified;
    const rate = _speedometer(progressBytes);
    const inRange = loaded <= total;

    bytesNotified = loaded;

    const data = {
      loaded,
      total,
      progress: total ? (loaded / total) : undefined,
      bytes: progressBytes,
      rate: rate ? rate : undefined,
      estimated: rate && total && inRange ? (total - loaded) / rate : undefined,
      event: e,
      lengthComputable: total != null,
      [isDownloadStream ? 'download' : 'upload']: true
    };

    listener(data);
  }, freq);
};

const progressEventDecorator = (total, throttled) => {
  const lengthComputable = total != null;

  return [(loaded) => throttled[0]({
    lengthComputable,
    total,
    loaded
  }), throttled[1]];
};

const asyncDecorator = (fn) => (...args) => utils$1.asap(() => fn(...args));

const isURLSameOrigin = platform.hasStandardBrowserEnv ? ((origin, isMSIE) => (url) => {
  url = new URL(url, platform.origin);

  return (
    origin.protocol === url.protocol &&
    origin.host === url.host &&
    (isMSIE || origin.port === url.port)
  );
})(
  new URL(platform.origin),
  platform.navigator && /(msie|trident)/i.test(platform.navigator.userAgent)
) : () => true;

const cookies = platform.hasStandardBrowserEnv ?

  // Standard browser envs support document.cookie
  {
    write(name, value, expires, path, domain, secure) {
      const cookie = [name + '=' + encodeURIComponent(value)];

      utils$1.isNumber(expires) && cookie.push('expires=' + new Date(expires).toGMTString());

      utils$1.isString(path) && cookie.push('path=' + path);

      utils$1.isString(domain) && cookie.push('domain=' + domain);

      secure === true && cookie.push('secure');

      document.cookie = cookie.join('; ');
    },

    read(name) {
      const match = document.cookie.match(new RegExp('(^|;\\s*)(' + name + ')=([^;]*)'));
      return (match ? decodeURIComponent(match[3]) : null);
    },

    remove(name) {
      this.write(name, '', Date.now() - 86400000);
    }
  }

  :

  // Non-standard browser env (web workers, react-native) lack needed support.
  {
    write() {},
    read() {
      return null;
    },
    remove() {}
  };

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
  return relativeURL
    ? baseURL.replace(/\/?\/$/, '') + '/' + relativeURL.replace(/^\/+/, '')
    : baseURL;
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
function buildFullPath(baseURL, requestedURL, allowAbsoluteUrls) {
  let isRelativeUrl = !isAbsoluteURL(requestedURL);
  if (baseURL && (isRelativeUrl || allowAbsoluteUrls == false)) {
    return combineURLs(baseURL, requestedURL);
  }
  return requestedURL;
}

const headersToObject = (thing) => thing instanceof AxiosHeaders$1 ? { ...thing } : thing;

/**
 * Config-specific merge-function which creates a new config-object
 * by merging two configuration objects together.
 *
 * @param {Object} config1
 * @param {Object} config2
 *
 * @returns {Object} New object resulting from merging config2 to config1
 */
function mergeConfig$1(config1, config2) {
  // eslint-disable-next-line no-param-reassign
  config2 = config2 || {};
  const config = {};

  function getMergedValue(target, source, prop, caseless) {
    if (utils$1.isPlainObject(target) && utils$1.isPlainObject(source)) {
      return utils$1.merge.call({caseless}, target, source);
    } else if (utils$1.isPlainObject(source)) {
      return utils$1.merge({}, source);
    } else if (utils$1.isArray(source)) {
      return source.slice();
    }
    return source;
  }

  // eslint-disable-next-line consistent-return
  function mergeDeepProperties(a, b, prop , caseless) {
    if (!utils$1.isUndefined(b)) {
      return getMergedValue(a, b, prop , caseless);
    } else if (!utils$1.isUndefined(a)) {
      return getMergedValue(undefined, a, prop , caseless);
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

  // eslint-disable-next-line consistent-return
  function mergeDirectKeys(a, b, prop) {
    if (prop in config2) {
      return getMergedValue(a, b);
    } else if (prop in config1) {
      return getMergedValue(undefined, a);
    }
  }

  const mergeMap = {
    url: valueFromConfig2,
    method: valueFromConfig2,
    data: valueFromConfig2,
    baseURL: defaultToConfig2,
    transformRequest: defaultToConfig2,
    transformResponse: defaultToConfig2,
    paramsSerializer: defaultToConfig2,
    timeout: defaultToConfig2,
    timeoutMessage: defaultToConfig2,
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
    responseEncoding: defaultToConfig2,
    validateStatus: mergeDirectKeys,
    headers: (a, b , prop) => mergeDeepProperties(headersToObject(a), headersToObject(b),prop, true)
  };

  utils$1.forEach(Object.keys(Object.assign({}, config1, config2)), function computeConfigValue(prop) {
    const merge = mergeMap[prop] || mergeDeepProperties;
    const configValue = merge(config1[prop], config2[prop], prop);
    (utils$1.isUndefined(configValue) && merge !== mergeDirectKeys) || (config[prop] = configValue);
  });

  return config;
}

const resolveConfig = (config) => {
  const newConfig = mergeConfig$1({}, config);

  let {data, withXSRFToken, xsrfHeaderName, xsrfCookieName, headers, auth} = newConfig;

  newConfig.headers = headers = AxiosHeaders$1.from(headers);

  newConfig.url = buildURL(buildFullPath(newConfig.baseURL, newConfig.url, newConfig.allowAbsoluteUrls), config.params, config.paramsSerializer);

  // HTTP basic authentication
  if (auth) {
    headers.set('Authorization', 'Basic ' +
      btoa((auth.username || '') + ':' + (auth.password ? unescape(encodeURIComponent(auth.password)) : ''))
    );
  }

  let contentType;

  if (utils$1.isFormData(data)) {
    if (platform.hasStandardBrowserEnv || platform.hasStandardBrowserWebWorkerEnv) {
      headers.setContentType(undefined); // Let the browser set it
    } else if ((contentType = headers.getContentType()) !== false) {
      // fix semicolon duplication issue for ReactNative FormData implementation
      const [type, ...tokens] = contentType ? contentType.split(';').map(token => token.trim()).filter(Boolean) : [];
      headers.setContentType([type || 'multipart/form-data', ...tokens].join('; '));
    }
  }

  // Add xsrf header
  // This is only done if running in a standard browser environment.
  // Specifically not if we're in a web worker, or react-native.

  if (platform.hasStandardBrowserEnv) {
    withXSRFToken && utils$1.isFunction(withXSRFToken) && (withXSRFToken = withXSRFToken(newConfig));

    if (withXSRFToken || (withXSRFToken !== false && isURLSameOrigin(newConfig.url))) {
      // Add xsrf header
      const xsrfValue = xsrfHeaderName && xsrfCookieName && cookies.read(xsrfCookieName);

      if (xsrfValue) {
        headers.set(xsrfHeaderName, xsrfValue);
      }
    }
  }

  return newConfig;
};

const isXHRAdapterSupported = typeof XMLHttpRequest !== 'undefined';

const xhrAdapter = isXHRAdapterSupported && function (config) {
  return new Promise(function dispatchXhrRequest(resolve, reject) {
    const _config = resolveConfig(config);
    let requestData = _config.data;
    const requestHeaders = AxiosHeaders$1.from(_config.headers).normalize();
    let {responseType, onUploadProgress, onDownloadProgress} = _config;
    let onCanceled;
    let uploadThrottled, downloadThrottled;
    let flushUpload, flushDownload;

    function done() {
      flushUpload && flushUpload(); // flush events
      flushDownload && flushDownload(); // flush events

      _config.cancelToken && _config.cancelToken.unsubscribe(onCanceled);

      _config.signal && _config.signal.removeEventListener('abort', onCanceled);
    }

    let request = new XMLHttpRequest();

    request.open(_config.method.toUpperCase(), _config.url, true);

    // Set the request timeout in MS
    request.timeout = _config.timeout;

    function onloadend() {
      if (!request) {
        return;
      }
      // Prepare the response
      const responseHeaders = AxiosHeaders$1.from(
        'getAllResponseHeaders' in request && request.getAllResponseHeaders()
      );
      const responseData = !responseType || responseType === 'text' || responseType === 'json' ?
        request.responseText : request.response;
      const response = {
        data: responseData,
        status: request.status,
        statusText: request.statusText,
        headers: responseHeaders,
        config,
        request
      };

      settle(function _resolve(value) {
        resolve(value);
        done();
      }, function _reject(err) {
        reject(err);
        done();
      }, response);

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
        if (request.status === 0 && !(request.responseURL && request.responseURL.indexOf('file:') === 0)) {
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

      // Clean up request
      request = null;
    };

    // Handle low level network errors
    request.onerror = function handleError() {
      // Real errors are hidden from us by the browser
      // onerror should only fire if it's a network error
      reject(new AxiosError$1('Network Error', AxiosError$1.ERR_NETWORK, config, request));

      // Clean up request
      request = null;
    };

    // Handle timeout
    request.ontimeout = function handleTimeout() {
      let timeoutErrorMessage = _config.timeout ? 'timeout of ' + _config.timeout + 'ms exceeded' : 'timeout exceeded';
      const transitional = _config.transitional || transitionalDefaults;
      if (_config.timeoutErrorMessage) {
        timeoutErrorMessage = _config.timeoutErrorMessage;
      }
      reject(new AxiosError$1(
        timeoutErrorMessage,
        transitional.clarifyTimeoutError ? AxiosError$1.ETIMEDOUT : AxiosError$1.ECONNABORTED,
        config,
        request));

      // Clean up request
      request = null;
    };

    // Remove Content-Type if data is undefined
    requestData === undefined && requestHeaders.setContentType(null);

    // Add headers to the request
    if ('setRequestHeader' in request) {
      utils$1.forEach(requestHeaders.toJSON(), function setRequestHeader(val, key) {
        request.setRequestHeader(key, val);
      });
    }

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
      ([downloadThrottled, flushDownload] = progressEventReducer(onDownloadProgress, true));
      request.addEventListener('progress', downloadThrottled);
    }

    // Not all browsers support upload events
    if (onUploadProgress && request.upload) {
      ([uploadThrottled, flushUpload] = progressEventReducer(onUploadProgress));

      request.upload.addEventListener('progress', uploadThrottled);

      request.upload.addEventListener('loadend', flushUpload);
    }

    if (_config.cancelToken || _config.signal) {
      // Handle cancellation
      // eslint-disable-next-line func-names
      onCanceled = cancel => {
        if (!request) {
          return;
        }
        reject(!cancel || cancel.type ? new CanceledError$1(null, config, request) : cancel);
        request.abort();
        request = null;
      };

      _config.cancelToken && _config.cancelToken.subscribe(onCanceled);
      if (_config.signal) {
        _config.signal.aborted ? onCanceled() : _config.signal.addEventListener('abort', onCanceled);
      }
    }

    const protocol = parseProtocol(_config.url);

    if (protocol && platform.protocols.indexOf(protocol) === -1) {
      reject(new AxiosError$1('Unsupported protocol ' + protocol + ':', AxiosError$1.ERR_BAD_REQUEST, config));
      return;
    }


    // Send the request
    request.send(requestData || null);
  });
};

const composeSignals = (signals, timeout) => {
  const {length} = (signals = signals ? signals.filter(Boolean) : []);

  if (timeout || length) {
    let controller = new AbortController();

    let aborted;

    const onabort = function (reason) {
      if (!aborted) {
        aborted = true;
        unsubscribe();
        const err = reason instanceof Error ? reason : this.reason;
        controller.abort(err instanceof AxiosError$1 ? err : new CanceledError$1(err instanceof Error ? err.message : err));
      }
    };

    let timer = timeout && setTimeout(() => {
      timer = null;
      onabort(new AxiosError$1(`timeout ${timeout} of ms exceeded`, AxiosError$1.ETIMEDOUT));
    }, timeout);

    const unsubscribe = () => {
      if (signals) {
        timer && clearTimeout(timer);
        timer = null;
        signals.forEach(signal => {
          signal.unsubscribe ? signal.unsubscribe(onabort) : signal.removeEventListener('abort', onabort);
        });
        signals = null;
      }
    };

    signals.forEach((signal) => signal.addEventListener('abort', onabort));

    const {signal} = controller;

    signal.unsubscribe = () => utils$1.asap(unsubscribe);

    return signal;
  }
};

const streamChunk = function* (chunk, chunkSize) {
  let len = chunk.byteLength;

  if (len < chunkSize) {
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
      const {done, value} = await reader.read();
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

  return new ReadableStream({
    async pull(controller) {
      try {
        const {done, value} = await iterator.next();

        if (done) {
         _onFinish();
          controller.close();
          return;
        }

        let len = value.byteLength;
        if (onProgress) {
          let loadedBytes = bytes += len;
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
    }
  }, {
    highWaterMark: 2
  })
};

const isFetchSupported = typeof fetch === 'function' && typeof Request === 'function' && typeof Response === 'function';
const isReadableStreamSupported = isFetchSupported && typeof ReadableStream === 'function';

// used only inside the fetch adapter
const encodeText = isFetchSupported && (typeof TextEncoder === 'function' ?
    ((encoder) => (str) => encoder.encode(str))(new TextEncoder()) :
    async (str) => new Uint8Array(await new Response(str).arrayBuffer())
);

const test = (fn, ...args) => {
  try {
    return !!fn(...args);
  } catch (e) {
    return false
  }
};

const supportsRequestStream = isReadableStreamSupported && test(() => {
  let duplexAccessed = false;

  const hasContentType = new Request(platform.origin, {
    body: new ReadableStream(),
    method: 'POST',
    get duplex() {
      duplexAccessed = true;
      return 'half';
    },
  }).headers.has('Content-Type');

  return duplexAccessed && !hasContentType;
});

const DEFAULT_CHUNK_SIZE = 64 * 1024;

const supportsResponseStream = isReadableStreamSupported &&
  test(() => utils$1.isReadableStream(new Response('').body));


const resolvers = {
  stream: supportsResponseStream && ((res) => res.body)
};

isFetchSupported && (((res) => {
  ['text', 'arrayBuffer', 'blob', 'formData', 'stream'].forEach(type => {
    !resolvers[type] && (resolvers[type] = utils$1.isFunction(res[type]) ? (res) => res[type]() :
      (_, config) => {
        throw new AxiosError$1(`Response type '${type}' is not supported`, AxiosError$1.ERR_NOT_SUPPORT, config);
      });
  });
})(new Response));

const getBodyLength = async (body) => {
  if (body == null) {
    return 0;
  }

  if(utils$1.isBlob(body)) {
    return body.size;
  }

  if(utils$1.isSpecCompliantForm(body)) {
    const _request = new Request(platform.origin, {
      method: 'POST',
      body,
    });
    return (await _request.arrayBuffer()).byteLength;
  }

  if(utils$1.isArrayBufferView(body) || utils$1.isArrayBuffer(body)) {
    return body.byteLength;
  }

  if(utils$1.isURLSearchParams(body)) {
    body = body + '';
  }

  if(utils$1.isString(body)) {
    return (await encodeText(body)).byteLength;
  }
};

const resolveBodyLength = async (headers, body) => {
  const length = utils$1.toFiniteNumber(headers.getContentLength());

  return length == null ? getBodyLength(body) : length;
};

const fetchAdapter = isFetchSupported && (async (config) => {
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
    fetchOptions
  } = resolveConfig(config);

  responseType = responseType ? (responseType + '').toLowerCase() : 'text';

  let composedSignal = composeSignals([signal, cancelToken && cancelToken.toAbortSignal()], timeout);

  let request;

  const unsubscribe = composedSignal && composedSignal.unsubscribe && (() => {
      composedSignal.unsubscribe();
  });

  let requestContentLength;

  try {
    if (
      onUploadProgress && supportsRequestStream && method !== 'get' && method !== 'head' &&
      (requestContentLength = await resolveBodyLength(headers, data)) !== 0
    ) {
      let _request = new Request(url, {
        method: 'POST',
        body: data,
        duplex: "half"
      });

      let contentTypeHeader;

      if (utils$1.isFormData(data) && (contentTypeHeader = _request.headers.get('content-type'))) {
        headers.setContentType(contentTypeHeader);
      }

      if (_request.body) {
        const [onProgress, flush] = progressEventDecorator(
          requestContentLength,
          progressEventReducer(asyncDecorator(onUploadProgress))
        );

        data = trackStream(_request.body, DEFAULT_CHUNK_SIZE, onProgress, flush);
      }
    }

    if (!utils$1.isString(withCredentials)) {
      withCredentials = withCredentials ? 'include' : 'omit';
    }

    // Cloudflare Workers throws when credentials are defined
    // see https://github.com/cloudflare/workerd/issues/902
    const isCredentialsSupported = "credentials" in Request.prototype;
    request = new Request(url, {
      ...fetchOptions,
      signal: composedSignal,
      method: method.toUpperCase(),
      headers: headers.normalize().toJSON(),
      body: data,
      duplex: "half",
      credentials: isCredentialsSupported ? withCredentials : undefined
    });

    let response = await fetch(request, fetchOptions);

    const isStreamResponse = supportsResponseStream && (responseType === 'stream' || responseType === 'response');

    if (supportsResponseStream && (onDownloadProgress || (isStreamResponse && unsubscribe))) {
      const options = {};

      ['status', 'statusText', 'headers'].forEach(prop => {
        options[prop] = response[prop];
      });

      const responseContentLength = utils$1.toFiniteNumber(response.headers.get('content-length'));

      const [onProgress, flush] = onDownloadProgress && progressEventDecorator(
        responseContentLength,
        progressEventReducer(asyncDecorator(onDownloadProgress), true)
      ) || [];

      response = new Response(
        trackStream(response.body, DEFAULT_CHUNK_SIZE, onProgress, () => {
          flush && flush();
          unsubscribe && unsubscribe();
        }),
        options
      );
    }

    responseType = responseType || 'text';

    let responseData = await resolvers[utils$1.findKey(resolvers, responseType) || 'text'](response, config);

    !isStreamResponse && unsubscribe && unsubscribe();

    return await new Promise((resolve, reject) => {
      settle(resolve, reject, {
        data: responseData,
        headers: AxiosHeaders$1.from(response.headers),
        status: response.status,
        statusText: response.statusText,
        config,
        request
      });
    })
  } catch (err) {
    unsubscribe && unsubscribe();

    if (err && err.name === 'TypeError' && /Load failed|fetch/i.test(err.message)) {
      throw Object.assign(
        new AxiosError$1('Network Error', AxiosError$1.ERR_NETWORK, config, request),
        {
          cause: err.cause || err
        }
      )
    }

    throw AxiosError$1.from(err, err && err.code, config, request);
  }
});

const knownAdapters = {
  http: httpAdapter,
  xhr: xhrAdapter,
  fetch: fetchAdapter
};

utils$1.forEach(knownAdapters, (fn, value) => {
  if (fn) {
    try {
      Object.defineProperty(fn, 'name', {value});
    } catch (e) {
      // eslint-disable-next-line no-empty
    }
    Object.defineProperty(fn, 'adapterName', {value});
  }
});

const renderReason = (reason) => `- ${reason}`;

const isResolvedHandle = (adapter) => utils$1.isFunction(adapter) || adapter === null || adapter === false;

const adapters = {
  getAdapter: (adapters) => {
    adapters = utils$1.isArray(adapters) ? adapters : [adapters];

    const {length} = adapters;
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

      if (adapter) {
        break;
      }

      rejectedReasons[id || '#' + i] = adapter;
    }

    if (!adapter) {

      const reasons = Object.entries(rejectedReasons)
        .map(([id, state]) => `adapter ${id} ` +
          (state === false ? 'is not supported by the environment' : 'is not available in the build')
        );

      let s = length ?
        (reasons.length > 1 ? 'since :\n' + reasons.map(renderReason).join('\n') : ' ' + renderReason(reasons[0])) :
        'as no adapter specified';

      throw new AxiosError$1(
        `There is no suitable adapter to dispatch the request ` + s,
        'ERR_NOT_SUPPORT'
      );
    }

    return adapter;
  },
  adapters: knownAdapters
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
 * Dispatch a request to the server using the configured adapter.
 *
 * @param {object} config The config that is to be used for the request
 *
 * @returns {Promise} The Promise to be fulfilled
 */
function dispatchRequest(config) {
  throwIfCancellationRequested(config);

  config.headers = AxiosHeaders$1.from(config.headers);

  // Transform request data
  config.data = transformData.call(
    config,
    config.transformRequest
  );

  if (['post', 'put', 'patch'].indexOf(config.method) !== -1) {
    config.headers.setContentType('application/x-www-form-urlencoded', false);
  }

  const adapter = adapters.getAdapter(config.adapter || defaults.adapter);

  return adapter(config).then(function onAdapterResolution(response) {
    throwIfCancellationRequested(config);

    // Transform response data
    response.data = transformData.call(
      config,
      config.transformResponse,
      response
    );

    response.headers = AxiosHeaders$1.from(response.headers);

    return response;
  }, function onAdapterRejection(reason) {
    if (!isCancel$1(reason)) {
      throwIfCancellationRequested(config);

      // Transform response data
      if (reason && reason.response) {
        reason.response.data = transformData.call(
          config,
          config.transformResponse,
          reason.response
        );
        reason.response.headers = AxiosHeaders$1.from(reason.response.headers);
      }
    }

    return Promise.reject(reason);
  });
}

const VERSION$1 = "1.10.0";

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
    return '[Axios v' + VERSION$1 + '] Transitional option \'' + opt + '\'' + desc + (message ? '. ' + message : '');
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
  }
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
  if (typeof options !== 'object') {
    throw new AxiosError$1('options must be an object', AxiosError$1.ERR_BAD_OPTION_VALUE);
  }
  const keys = Object.keys(options);
  let i = keys.length;
  while (i-- > 0) {
    const opt = keys[i];
    const validator = schema[opt];
    if (validator) {
      const value = options[opt];
      const result = value === undefined || validator(value, opt, options);
      if (result !== true) {
        throw new AxiosError$1('option ' + opt + ' must be ' + result, AxiosError$1.ERR_BAD_OPTION_VALUE);
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
  validators: validators$1
};

const validators = validator.validators;

/**
 * Create a new instance of Axios
 *
 * @param {Object} instanceConfig The default config for the instance
 *
 * @return {Axios} A new instance of Axios
 */
let Axios$1 = class Axios {
  constructor(instanceConfig) {
    this.defaults = instanceConfig || {};
    this.interceptors = {
      request: new InterceptorManager(),
      response: new InterceptorManager()
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
        let dummy = {};

        Error.captureStackTrace ? Error.captureStackTrace(dummy) : (dummy = new Error());

        // slice off the Error: ... line
        const stack = dummy.stack ? dummy.stack.replace(/^.+\n/, '') : '';
        try {
          if (!err.stack) {
            err.stack = stack;
            // match without the 2 top stack lines
          } else if (stack && !String(err.stack).endsWith(stack.replace(/^.+\n.+\n/, ''))) {
            err.stack += '\n' + stack;
          }
        } catch (e) {
          // ignore the case where "stack" is an un-writable property
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

    config = mergeConfig$1(this.defaults, config);

    const {transitional, paramsSerializer, headers} = config;

    if (transitional !== undefined) {
      validator.assertOptions(transitional, {
        silentJSONParsing: validators.transitional(validators.boolean),
        forcedJSONParsing: validators.transitional(validators.boolean),
        clarifyTimeoutError: validators.transitional(validators.boolean)
      }, false);
    }

    if (paramsSerializer != null) {
      if (utils$1.isFunction(paramsSerializer)) {
        config.paramsSerializer = {
          serialize: paramsSerializer
        };
      } else {
        validator.assertOptions(paramsSerializer, {
          encode: validators.function,
          serialize: validators.function
        }, true);
      }
    }

    // Set config.allowAbsoluteUrls
    if (config.allowAbsoluteUrls !== undefined) ; else if (this.defaults.allowAbsoluteUrls !== undefined) {
      config.allowAbsoluteUrls = this.defaults.allowAbsoluteUrls;
    } else {
      config.allowAbsoluteUrls = true;
    }

    validator.assertOptions(config, {
      baseUrl: validators.spelling('baseURL'),
      withXsrfToken: validators.spelling('withXSRFToken')
    }, true);

    // Set config.method
    config.method = (config.method || this.defaults.method || 'get').toLowerCase();

    // Flatten headers
    let contextHeaders = headers && utils$1.merge(
      headers.common,
      headers[config.method]
    );

    headers && utils$1.forEach(
      ['delete', 'get', 'head', 'post', 'put', 'patch', 'common'],
      (method) => {
        delete headers[method];
      }
    );

    config.headers = AxiosHeaders$1.concat(contextHeaders, headers);

    // filter out skipped interceptors
    const requestInterceptorChain = [];
    let synchronousRequestInterceptors = true;
    this.interceptors.request.forEach(function unshiftRequestInterceptors(interceptor) {
      if (typeof interceptor.runWhen === 'function' && interceptor.runWhen(config) === false) {
        return;
      }

      synchronousRequestInterceptors = synchronousRequestInterceptors && interceptor.synchronous;

      requestInterceptorChain.unshift(interceptor.fulfilled, interceptor.rejected);
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
      chain.unshift.apply(chain, requestInterceptorChain);
      chain.push.apply(chain, responseInterceptorChain);
      len = chain.length;

      promise = Promise.resolve(config);

      while (i < len) {
        promise = promise.then(chain[i++], chain[i++]);
      }

      return promise;
    }

    len = requestInterceptorChain.length;

    let newConfig = config;

    i = 0;

    while (i < len) {
      const onFulfilled = requestInterceptorChain[i++];
      const onRejected = requestInterceptorChain[i++];
      try {
        newConfig = onFulfilled(newConfig);
      } catch (error) {
        onRejected.call(this, error);
        break;
      }
    }

    try {
      promise = dispatchRequest.call(this, newConfig);
    } catch (error) {
      return Promise.reject(error);
    }

    i = 0;
    len = responseInterceptorChain.length;

    while (i < len) {
      promise = promise.then(responseInterceptorChain[i++], responseInterceptorChain[i++]);
    }

    return promise;
  }

  getUri(config) {
    config = mergeConfig$1(this.defaults, config);
    const fullPath = buildFullPath(config.baseURL, config.url, config.allowAbsoluteUrls);
    return buildURL(fullPath, config.params, config.paramsSerializer);
  }
};

// Provide aliases for supported request methods
utils$1.forEach(['delete', 'get', 'head', 'options'], function forEachMethodNoData(method) {
  /*eslint func-names:0*/
  Axios$1.prototype[method] = function(url, config) {
    return this.request(mergeConfig$1(config || {}, {
      method,
      url,
      data: (config || {}).data
    }));
  };
});

utils$1.forEach(['post', 'put', 'patch'], function forEachMethodWithData(method) {
  /*eslint func-names:0*/

  function generateHTTPMethod(isForm) {
    return function httpMethod(url, data, config) {
      return this.request(mergeConfig$1(config || {}, {
        method,
        headers: isForm ? {
          'Content-Type': 'multipart/form-data'
        } : {},
        url,
        data
      }));
    };
  }

  Axios$1.prototype[method] = generateHTTPMethod();

  Axios$1.prototype[method + 'Form'] = generateHTTPMethod(true);
});

/**
 * A `CancelToken` is an object that can be used to request cancellation of an operation.
 *
 * @param {Function} executor The executor function.
 *
 * @returns {CancelToken}
 */
let CancelToken$1 = class CancelToken {
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
    this.promise.then(cancel => {
      if (!token._listeners) return;

      let i = token._listeners.length;

      while (i-- > 0) {
        token._listeners[i](cancel);
      }
      token._listeners = null;
    });

    // eslint-disable-next-line func-names
    this.promise.then = onfulfilled => {
      let _resolve;
      // eslint-disable-next-line func-names
      const promise = new Promise(resolve => {
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
      cancel
    };
  }
};

/**
 * Syntactic sugar for invoking a function and expanding an array for arguments.
 *
 * Common use case would be to use `Function.prototype.apply`.
 *
 *  ```js
 *  function f(x, y, z) {}
 *  var args = [1, 2, 3];
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
function spread$1(callback) {
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
function isAxiosError$1(payload) {
  return utils$1.isObject(payload) && (payload.isAxiosError === true);
}

const HttpStatusCode$1 = {
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
  PayloadTooLarge: 413,
  UriTooLong: 414,
  UnsupportedMediaType: 415,
  RangeNotSatisfiable: 416,
  ExpectationFailed: 417,
  ImATeapot: 418,
  MisdirectedRequest: 421,
  UnprocessableEntity: 422,
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
};

Object.entries(HttpStatusCode$1).forEach(([key, value]) => {
  HttpStatusCode$1[value] = key;
});

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
  utils$1.extend(instance, Axios$1.prototype, context, {allOwnKeys: true});

  // Copy context to instance
  utils$1.extend(instance, context, null, {allOwnKeys: true});

  // Factory for creating new instances
  instance.create = function create(instanceConfig) {
    return createInstance(mergeConfig$1(defaultConfig, instanceConfig));
  };

  return instance;
}

// Create the default instance to be exported
const axios = createInstance(defaults);

// Expose Axios class to allow class inheritance
axios.Axios = Axios$1;

// Expose Cancel & CancelToken
axios.CanceledError = CanceledError$1;
axios.CancelToken = CancelToken$1;
axios.isCancel = isCancel$1;
axios.VERSION = VERSION$1;
axios.toFormData = toFormData$1;

// Expose AxiosError class
axios.AxiosError = AxiosError$1;

// alias for CanceledError for backward compatibility
axios.Cancel = axios.CanceledError;

// Expose all/spread
axios.all = function all(promises) {
  return Promise.all(promises);
};

axios.spread = spread$1;

// Expose isAxiosError
axios.isAxiosError = isAxiosError$1;

// Expose mergeConfig
axios.mergeConfig = mergeConfig$1;

axios.AxiosHeaders = AxiosHeaders$1;

axios.formToJSON = thing => formDataToJSON(utils$1.isHTMLForm(thing) ? new FormData(thing) : thing);

axios.getAdapter = adapters.getAdapter;

axios.HttpStatusCode = HttpStatusCode$1;

axios.default = axios;

// This module is intended to unwrap Axios default export as named.
// Keep top-level export same with static properties
// so that it can keep same with es module or cjs
const {
  Axios,
  AxiosError,
  CanceledError,
  isCancel,
  CancelToken,
  VERSION,
  all,
  Cancel,
  isAxiosError,
  spread,
  toFormData,
  AxiosHeaders,
  HttpStatusCode,
  formToJSON,
  getAdapter,
  mergeConfig
} = axios;

var dayjs_min = {exports: {}};

(function (module, exports) {
	!function(t,e){module.exports=e();}(commonjsGlobal,(function(){var t=1e3,e=6e4,n=36e5,r="millisecond",i="second",s="minute",u="hour",a="day",o="week",c="month",f="quarter",h="year",d="date",l="Invalid Date",$=/^(\d{4})[-/]?(\d{1,2})?[-/]?(\d{0,2})[Tt\s]*(\d{1,2})?:?(\d{1,2})?:?(\d{1,2})?[.:]?(\d+)?$/,y=/\[([^\]]+)]|Y{1,4}|M{1,4}|D{1,2}|d{1,4}|H{1,2}|h{1,2}|a|A|m{1,2}|s{1,2}|Z{1,2}|SSS/g,M={name:"en",weekdays:"Sunday_Monday_Tuesday_Wednesday_Thursday_Friday_Saturday".split("_"),months:"January_February_March_April_May_June_July_August_September_October_November_December".split("_"),ordinal:function(t){var e=["th","st","nd","rd"],n=t%100;return "["+t+(e[(n-20)%10]||e[n]||e[0])+"]"}},m=function(t,e,n){var r=String(t);return !r||r.length>=e?t:""+Array(e+1-r.length).join(n)+t},v={s:m,z:function(t){var e=-t.utcOffset(),n=Math.abs(e),r=Math.floor(n/60),i=n%60;return (e<=0?"+":"-")+m(r,2,"0")+":"+m(i,2,"0")},m:function t(e,n){if(e.date()<n.date())return -t(n,e);var r=12*(n.year()-e.year())+(n.month()-e.month()),i=e.clone().add(r,c),s=n-i<0,u=e.clone().add(r+(s?-1:1),c);return +(-(r+(n-i)/(s?i-u:u-i))||0)},a:function(t){return t<0?Math.ceil(t)||0:Math.floor(t)},p:function(t){return {M:c,y:h,w:o,d:a,D:d,h:u,m:s,s:i,ms:r,Q:f}[t]||String(t||"").toLowerCase().replace(/s$/,"")},u:function(t){return void 0===t}},g="en",D={};D[g]=M;var p="$isDayjsObject",S=function(t){return t instanceof _||!(!t||!t[p])},w=function t(e,n,r){var i;if(!e)return g;if("string"==typeof e){var s=e.toLowerCase();D[s]&&(i=s),n&&(D[s]=n,i=s);var u=e.split("-");if(!i&&u.length>1)return t(u[0])}else {var a=e.name;D[a]=e,i=a;}return !r&&i&&(g=i),i||!r&&g},O=function(t,e){if(S(t))return t.clone();var n="object"==typeof e?e:{};return n.date=t,n.args=arguments,new _(n)},b=v;b.l=w,b.i=S,b.w=function(t,e){return O(t,{locale:e.$L,utc:e.$u,x:e.$x,$offset:e.$offset})};var _=function(){function M(t){this.$L=w(t.locale,null,true),this.parse(t),this.$x=this.$x||t.x||{},this[p]=true;}var m=M.prototype;return m.parse=function(t){this.$d=function(t){var e=t.date,n=t.utc;if(null===e)return new Date(NaN);if(b.u(e))return new Date;if(e instanceof Date)return new Date(e);if("string"==typeof e&&!/Z$/i.test(e)){var r=e.match($);if(r){var i=r[2]-1||0,s=(r[7]||"0").substring(0,3);return n?new Date(Date.UTC(r[1],i,r[3]||1,r[4]||0,r[5]||0,r[6]||0,s)):new Date(r[1],i,r[3]||1,r[4]||0,r[5]||0,r[6]||0,s)}}return new Date(e)}(t),this.init();},m.init=function(){var t=this.$d;this.$y=t.getFullYear(),this.$M=t.getMonth(),this.$D=t.getDate(),this.$W=t.getDay(),this.$H=t.getHours(),this.$m=t.getMinutes(),this.$s=t.getSeconds(),this.$ms=t.getMilliseconds();},m.$utils=function(){return b},m.isValid=function(){return !(this.$d.toString()===l)},m.isSame=function(t,e){var n=O(t);return this.startOf(e)<=n&&n<=this.endOf(e)},m.isAfter=function(t,e){return O(t)<this.startOf(e)},m.isBefore=function(t,e){return this.endOf(e)<O(t)},m.$g=function(t,e,n){return b.u(t)?this[e]:this.set(n,t)},m.unix=function(){return Math.floor(this.valueOf()/1e3)},m.valueOf=function(){return this.$d.getTime()},m.startOf=function(t,e){var n=this,r=!!b.u(e)||e,f=b.p(t),l=function(t,e){var i=b.w(n.$u?Date.UTC(n.$y,e,t):new Date(n.$y,e,t),n);return r?i:i.endOf(a)},$=function(t,e){return b.w(n.toDate()[t].apply(n.toDate("s"),(r?[0,0,0,0]:[23,59,59,999]).slice(e)),n)},y=this.$W,M=this.$M,m=this.$D,v="set"+(this.$u?"UTC":"");switch(f){case h:return r?l(1,0):l(31,11);case c:return r?l(1,M):l(0,M+1);case o:var g=this.$locale().weekStart||0,D=(y<g?y+7:y)-g;return l(r?m-D:m+(6-D),M);case a:case d:return $(v+"Hours",0);case u:return $(v+"Minutes",1);case s:return $(v+"Seconds",2);case i:return $(v+"Milliseconds",3);default:return this.clone()}},m.endOf=function(t){return this.startOf(t,false)},m.$set=function(t,e){var n,o=b.p(t),f="set"+(this.$u?"UTC":""),l=(n={},n[a]=f+"Date",n[d]=f+"Date",n[c]=f+"Month",n[h]=f+"FullYear",n[u]=f+"Hours",n[s]=f+"Minutes",n[i]=f+"Seconds",n[r]=f+"Milliseconds",n)[o],$=o===a?this.$D+(e-this.$W):e;if(o===c||o===h){var y=this.clone().set(d,1);y.$d[l]($),y.init(),this.$d=y.set(d,Math.min(this.$D,y.daysInMonth())).$d;}else l&&this.$d[l]($);return this.init(),this},m.set=function(t,e){return this.clone().$set(t,e)},m.get=function(t){return this[b.p(t)]()},m.add=function(r,f){var d,l=this;r=Number(r);var $=b.p(f),y=function(t){var e=O(l);return b.w(e.date(e.date()+Math.round(t*r)),l)};if($===c)return this.set(c,this.$M+r);if($===h)return this.set(h,this.$y+r);if($===a)return y(1);if($===o)return y(7);var M=(d={},d[s]=e,d[u]=n,d[i]=t,d)[$]||1,m=this.$d.getTime()+r*M;return b.w(m,this)},m.subtract=function(t,e){return this.add(-1*t,e)},m.format=function(t){var e=this,n=this.$locale();if(!this.isValid())return n.invalidDate||l;var r=t||"YYYY-MM-DDTHH:mm:ssZ",i=b.z(this),s=this.$H,u=this.$m,a=this.$M,o=n.weekdays,c=n.months,f=n.meridiem,h=function(t,n,i,s){return t&&(t[n]||t(e,r))||i[n].slice(0,s)},d=function(t){return b.s(s%12||12,t,"0")},$=f||function(t,e,n){var r=t<12?"AM":"PM";return n?r.toLowerCase():r};return r.replace(y,(function(t,r){return r||function(t){switch(t){case "YY":return String(e.$y).slice(-2);case "YYYY":return b.s(e.$y,4,"0");case "M":return a+1;case "MM":return b.s(a+1,2,"0");case "MMM":return h(n.monthsShort,a,c,3);case "MMMM":return h(c,a);case "D":return e.$D;case "DD":return b.s(e.$D,2,"0");case "d":return String(e.$W);case "dd":return h(n.weekdaysMin,e.$W,o,2);case "ddd":return h(n.weekdaysShort,e.$W,o,3);case "dddd":return o[e.$W];case "H":return String(s);case "HH":return b.s(s,2,"0");case "h":return d(1);case "hh":return d(2);case "a":return $(s,u,true);case "A":return $(s,u,false);case "m":return String(u);case "mm":return b.s(u,2,"0");case "s":return String(e.$s);case "ss":return b.s(e.$s,2,"0");case "SSS":return b.s(e.$ms,3,"0");case "Z":return i}return null}(t)||i.replace(":","")}))},m.utcOffset=function(){return 15*-Math.round(this.$d.getTimezoneOffset()/15)},m.diff=function(r,d,l){var $,y=this,M=b.p(d),m=O(r),v=(m.utcOffset()-this.utcOffset())*e,g=this-m,D=function(){return b.m(y,m)};switch(M){case h:$=D()/12;break;case c:$=D();break;case f:$=D()/3;break;case o:$=(g-v)/6048e5;break;case a:$=(g-v)/864e5;break;case u:$=g/n;break;case s:$=g/e;break;case i:$=g/t;break;default:$=g;}return l?$:b.a($)},m.daysInMonth=function(){return this.endOf(c).$D},m.$locale=function(){return D[this.$L]},m.locale=function(t,e){if(!t)return this.$L;var n=this.clone(),r=w(t,e,true);return r&&(n.$L=r),n},m.clone=function(){return b.w(this.$d,this)},m.toDate=function(){return new Date(this.valueOf())},m.toJSON=function(){return this.isValid()?this.toISOString():null},m.toISOString=function(){return this.$d.toISOString()},m.toString=function(){return this.$d.toUTCString()},M}(),k=_.prototype;return O.prototype=k,[["$ms",r],["$s",i],["$m",s],["$H",u],["$W",a],["$M",c],["$y",h],["$D",d]].forEach((function(t){k[t[1]]=function(e){return this.$g(e,t[0],t[1])};})),O.extend=function(t,e){return t.$i||(t(e,_,O),t.$i=true),O},O.locale=w,O.isDayjs=S,O.unix=function(t){return O(1e3*t)},O.en=D[g],O.Ls=D,O.p={},O})); 
} (dayjs_min));

var dayjs_minExports = dayjs_min.exports;
const dayjs = /*@__PURE__*/getDefaultExportFromCjs(dayjs_minExports);

var duration$1 = {exports: {}};

(function (module, exports) {
	!function(t,s){module.exports=s();}(commonjsGlobal,(function(){var t,s,n=1e3,i=6e4,e=36e5,r=864e5,o=/\[([^\]]+)]|Y{1,4}|M{1,4}|D{1,2}|d{1,4}|H{1,2}|h{1,2}|a|A|m{1,2}|s{1,2}|Z{1,2}|SSS/g,u=31536e6,d=2628e6,a=/^(-|\+)?P(?:([-+]?[0-9,.]*)Y)?(?:([-+]?[0-9,.]*)M)?(?:([-+]?[0-9,.]*)W)?(?:([-+]?[0-9,.]*)D)?(?:T(?:([-+]?[0-9,.]*)H)?(?:([-+]?[0-9,.]*)M)?(?:([-+]?[0-9,.]*)S)?)?$/,h={years:u,months:d,days:r,hours:e,minutes:i,seconds:n,milliseconds:1,weeks:6048e5},c=function(t){return t instanceof g},f=function(t,s,n){return new g(t,n,s.$l)},m=function(t){return s.p(t)+"s"},l=function(t){return t<0},$=function(t){return l(t)?Math.ceil(t):Math.floor(t)},y=function(t){return Math.abs(t)},v=function(t,s){return t?l(t)?{negative:true,format:""+y(t)+s}:{negative:false,format:""+t+s}:{negative:false,format:""}},g=function(){function l(t,s,n){var i=this;if(this.$d={},this.$l=n,void 0===t&&(this.$ms=0,this.parseFromMilliseconds()),s)return f(t*h[m(s)],this);if("number"==typeof t)return this.$ms=t,this.parseFromMilliseconds(),this;if("object"==typeof t)return Object.keys(t).forEach((function(s){i.$d[m(s)]=t[s];})),this.calMilliseconds(),this;if("string"==typeof t){var e=t.match(a);if(e){var r=e.slice(2).map((function(t){return null!=t?Number(t):0}));return this.$d.years=r[0],this.$d.months=r[1],this.$d.weeks=r[2],this.$d.days=r[3],this.$d.hours=r[4],this.$d.minutes=r[5],this.$d.seconds=r[6],this.calMilliseconds(),this}}return this}var y=l.prototype;return y.calMilliseconds=function(){var t=this;this.$ms=Object.keys(this.$d).reduce((function(s,n){return s+(t.$d[n]||0)*h[n]}),0);},y.parseFromMilliseconds=function(){var t=this.$ms;this.$d.years=$(t/u),t%=u,this.$d.months=$(t/d),t%=d,this.$d.days=$(t/r),t%=r,this.$d.hours=$(t/e),t%=e,this.$d.minutes=$(t/i),t%=i,this.$d.seconds=$(t/n),t%=n,this.$d.milliseconds=t;},y.toISOString=function(){var t=v(this.$d.years,"Y"),s=v(this.$d.months,"M"),n=+this.$d.days||0;this.$d.weeks&&(n+=7*this.$d.weeks);var i=v(n,"D"),e=v(this.$d.hours,"H"),r=v(this.$d.minutes,"M"),o=this.$d.seconds||0;this.$d.milliseconds&&(o+=this.$d.milliseconds/1e3,o=Math.round(1e3*o)/1e3);var u=v(o,"S"),d=t.negative||s.negative||i.negative||e.negative||r.negative||u.negative,a=e.format||r.format||u.format?"T":"",h=(d?"-":"")+"P"+t.format+s.format+i.format+a+e.format+r.format+u.format;return "P"===h||"-P"===h?"P0D":h},y.toJSON=function(){return this.toISOString()},y.format=function(t){var n=t||"YYYY-MM-DDTHH:mm:ss",i={Y:this.$d.years,YY:s.s(this.$d.years,2,"0"),YYYY:s.s(this.$d.years,4,"0"),M:this.$d.months,MM:s.s(this.$d.months,2,"0"),D:this.$d.days,DD:s.s(this.$d.days,2,"0"),H:this.$d.hours,HH:s.s(this.$d.hours,2,"0"),m:this.$d.minutes,mm:s.s(this.$d.minutes,2,"0"),s:this.$d.seconds,ss:s.s(this.$d.seconds,2,"0"),SSS:s.s(this.$d.milliseconds,3,"0")};return n.replace(o,(function(t,s){return s||String(i[t])}))},y.as=function(t){return this.$ms/h[m(t)]},y.get=function(t){var s=this.$ms,n=m(t);return "milliseconds"===n?s%=1e3:s="weeks"===n?$(s/h[n]):this.$d[n],s||0},y.add=function(t,s,n){var i;return i=s?t*h[m(s)]:c(t)?t.$ms:f(t,this).$ms,f(this.$ms+i*(n?-1:1),this)},y.subtract=function(t,s){return this.add(t,s,true)},y.locale=function(t){var s=this.clone();return s.$l=t,s},y.clone=function(){return f(this.$ms,this)},y.humanize=function(s){return t().add(this.$ms,"ms").locale(this.$l).fromNow(!s)},y.valueOf=function(){return this.asMilliseconds()},y.milliseconds=function(){return this.get("milliseconds")},y.asMilliseconds=function(){return this.as("milliseconds")},y.seconds=function(){return this.get("seconds")},y.asSeconds=function(){return this.as("seconds")},y.minutes=function(){return this.get("minutes")},y.asMinutes=function(){return this.as("minutes")},y.hours=function(){return this.get("hours")},y.asHours=function(){return this.as("hours")},y.days=function(){return this.get("days")},y.asDays=function(){return this.as("days")},y.weeks=function(){return this.get("weeks")},y.asWeeks=function(){return this.as("weeks")},y.months=function(){return this.get("months")},y.asMonths=function(){return this.as("months")},y.years=function(){return this.get("years")},y.asYears=function(){return this.as("years")},l}(),p=function(t,s,n){return t.add(s.years()*n,"y").add(s.months()*n,"M").add(s.days()*n,"d").add(s.hours()*n,"h").add(s.minutes()*n,"m").add(s.seconds()*n,"s").add(s.milliseconds()*n,"ms")};return function(n,i,e){t=e,s=e().$utils(),e.duration=function(t,s){var n=e.locale();return f(t,{$l:n},s)},e.isDuration=c;var r=i.prototype.add,o=i.prototype.subtract;i.prototype.add=function(t,s){return c(t)?p(this,t,1):r.bind(this)(t,s)},i.prototype.subtract=function(t,s){return c(t)?p(this,t,-1):o.bind(this)(t,s)};}})); 
} (duration$1));

var durationExports = duration$1.exports;
const duration = /*@__PURE__*/getDefaultExportFromCjs(durationExports);

const {createTextVNode:_createTextVNode,resolveComponent:_resolveComponent,withCtx:_withCtx,createVNode:_createVNode,createElementVNode:_createElementVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,toDisplayString:_toDisplayString,createElementBlock:_createElementBlock,mergeProps:_mergeProps,normalizeStyle:_normalizeStyle,normalizeClass:_normalizeClass,renderList:_renderList,Fragment:_Fragment} = await importShared('vue');


const _hoisted_1 = { class: "status-page-container" };
const _hoisted_2 = { class: "card-header-modern" };
const _hoisted_3 = { class: "card-header-left" };
const _hoisted_4 = { class: "card-icon-wrapper card-icon-success" };
const _hoisted_5 = { class: "pve-header-info" };
const _hoisted_6 = { class: "pve-header-info-item" };
const _hoisted_7 = { class: "pve-header-value" };
const _hoisted_8 = { class: "pve-header-info-item" };
const _hoisted_9 = { class: "pve-header-value" };
const _hoisted_10 = { class: "pve-header-info-item" };
const _hoisted_11 = { class: "pve-header-value" };
const _hoisted_12 = { class: "pve-header-info-item" };
const _hoisted_13 = { class: "pve-header-value" };
const _hoisted_14 = {
  key: 0,
  class: "pve-header-info-item"
};
const _hoisted_15 = { class: "pve-header-value text-caption" };
const _hoisted_16 = { class: "host-action-btns-modern" };
const _hoisted_17 = { class: "card-body-modern" };
const _hoisted_18 = {
  key: 0,
  class: "pve-info-grid"
};
const _hoisted_19 = { class: "pve-info-right" };
const _hoisted_20 = { class: "status-item-modern" };
const _hoisted_21 = { class: "status-item-header" };
const _hoisted_22 = { class: "resource-info" };
const _hoisted_23 = { class: "resource-text-compact" };
const _hoisted_24 = { class: "resource-model" };
const _hoisted_25 = { class: "resource-progress-wrapper" };
const _hoisted_26 = { class: "resource-percent" };
const _hoisted_27 = { class: "status-item-modern" };
const _hoisted_28 = { class: "status-item-header" };
const _hoisted_29 = { class: "resource-info" };
const _hoisted_30 = { class: "resource-text-compact" };
const _hoisted_31 = { class: "resource-model" };
const _hoisted_32 = { class: "resource-progress-wrapper" };
const _hoisted_33 = { class: "resource-percent" };
const _hoisted_34 = { class: "status-item-modern" };
const _hoisted_35 = { class: "status-item-header" };
const _hoisted_36 = { class: "resource-info" };
const _hoisted_37 = { class: "resource-text-compact" };
const _hoisted_38 = { class: "resource-model" };
const _hoisted_39 = { class: "resource-progress-wrapper" };
const _hoisted_40 = { class: "resource-percent" };
const _hoisted_41 = {
  key: 0,
  class: "status-item-modern"
};
const _hoisted_42 = { class: "status-item-header" };
const _hoisted_43 = { class: "resource-info" };
const _hoisted_44 = { class: "resource-text-compact" };
const _hoisted_45 = { class: "resource-model" };
const _hoisted_46 = { class: "resource-progress-wrapper" };
const _hoisted_47 = { class: "resource-percent" };
const _hoisted_48 = {
  key: 1,
  class: "status-item-modern"
};
const _hoisted_49 = { class: "status-item-header" };
const _hoisted_50 = { class: "resource-info" };
const _hoisted_51 = { class: "resource-text-compact" };
const _hoisted_52 = { class: "resource-model" };
const _hoisted_53 = { class: "resource-progress-wrapper" };
const _hoisted_54 = { class: "resource-percent" };
const _hoisted_55 = {
  key: 1,
  class: "offline-state"
};
const _hoisted_56 = { class: "offline-error text-caption" };
const _hoisted_57 = { class: "card-header-modern" };
const _hoisted_58 = { class: "card-header-left" };
const _hoisted_59 = { class: "card-icon-wrapper card-icon-info" };
const _hoisted_60 = { class: "container-header-summary" };
const _hoisted_61 = { class: "header-summary-item" };
const _hoisted_62 = { class: "header-summary-item" };
const _hoisted_63 = { class: "header-summary-item" };
const _hoisted_64 = { class: "header-summary-item" };
const _hoisted_65 = { class: "header-summary-item" };
const _hoisted_66 = { class: "card-body-modern" };
const _hoisted_67 = { key: 0 };
const _hoisted_68 = { key: 0 };
const _hoisted_69 = ["innerHTML"];
const _hoisted_70 = {
  class: "d-flex justify-end align-center",
  style: {"gap":"4px"}
};
const _hoisted_71 = { key: 1 };
const _hoisted_72 = { class: "d-flex align-center mb-1" };
const _hoisted_73 = {
  class: "font-weight-bold",
  style: {"font-size":"1.1em"}
};
const _hoisted_74 = {
  class: "d-flex align-center mb-1",
  style: {"font-size":"0.95em","color":"#90caf9"}
};
const _hoisted_75 = {
  class: "d-flex align-center mb-1",
  style: {"font-size":"0.95em"}
};
const _hoisted_76 = ["innerHTML"];
const _hoisted_77 = {
  class: "mobile-actions d-flex align-center",
  style: {"gap":"8px","flex-wrap":"wrap"}
};
const _hoisted_78 = { class: "mb-2" };
const _hoisted_79 = {
  class: "font-weight-bold",
  style: {"color":"#d32f2f"}
};
const _hoisted_80 = { key: 0 };
const _hoisted_81 = { class: "grey--text text--darken-1" };
const _hoisted_82 = {
  class: "d-flex align-center",
  style: {"gap":"4px"}
};
const _hoisted_83 = { style: {"font-size":"1.6rem","margin-right":"8px"} };
const _hoisted_84 = { style: {"font-size":"1.1rem","font-weight":"600","color":"#00eaff","margin-bottom":"8px"} };
const _hoisted_85 = { style: {"margin-bottom":"8px","color":"#2196f3"} };
const _hoisted_86 = { style: {"color":"#00eaff"} };
const _hoisted_87 = { style: {"margin-top":"12px","color":"#ffb300","font-size":"1.05rem"} };
const _hoisted_88 = { style: {"font-size":"1.1em"} };
const _hoisted_89 = {
  key: 0,
  style: {"color":"#d32f2f"}
};
const _hoisted_90 = {
  key: 1,
  style: {"color":"#1976d2"}
};

const {ref,onMounted,computed} = await importShared('vue');

const _sfc_main = {
  __name: 'Page',
  props: { api: { type: [Object, Function], required: true } },
  emits: ['switch', 'close'],
  setup(__props, { emit: __emit }) {

dayjs.extend(duration);
// PVE标签色数组（可根据实际PVE配色调整）
const pveTagColors = [
  '#e573b7', // 粉
  '#bdb76b', // 黄褐
  '#81c784', // 绿
  '#ba68c8', // 紫
  '#ffd54f', // 黄
  '#64b5f6', // 蓝
  '#4db6ac', // 青
  '#f06292', // 粉2
  '#9575cd', // 紫2
  '#90caf9'  // 浅蓝
];
function getPveTagColor(tag) {
  // 简单hash算法，将标签内容hash到颜色数组
  let hash = 0;
  for (let i = 0; i < tag.length; i++) {
    hash = ((hash << 5) - hash) + tag.charCodeAt(i);
    hash |= 0;
  }
  const idx = Math.abs(hash) % pveTagColors.length;
  return pveTagColors[idx];
}
const props = __props;

const status = ref({});
const backupFiles = ref([]);
const history = ref([]);
const loadingBackup = ref(false);
const loadingRestore = ref(false);
const loadingClear = ref(false);
const loadingStopTasks = ref(false);
const showRestoreDialog = ref(false);
const selectedRestoreFile = ref(null);
const restoreVmid = ref('');
const restoreForce = ref(false);
const restoreSkipExisting = ref(true);
const restoreDisk = ref('');
const storageOptions = ref([]);
const loadingStorages = ref(false);
const snackbar = ref({ show: false, text: '', color: 'success', timeout: 3000 });
const deleteLoading = ref(null);
const showDeleteDialog = ref(false);
const deleteTarget = ref(null);
const showHistoryDialog = ref(false);
const pveStatus = ref({});
const containerStatus = ref([]);
const containerHeaders = [
  { text: 'ID', value: 'vmid' },
  { text: '名称', value: 'displayName' },
  { text: '类型', value: 'type' },
  { text: '状态', value: 'status' },
  { text: '标签', value: 'tags' },
  { text: '运行时间', value: 'uptime' },
  { text: '操作', value: 'actions', sortable: false },
];
const showBackupFilesDialog = ref(false);
const backupFileHeaders = [
  { text: '文件名', value: 'filename' },
  { text: '类型', value: 'source' },
  { text: '大小(MB)', value: 'size_mb' },
  { text: '日期', value: 'date' },
  { text: '时间', value: 'time' },
  { text: '备份路径', value: 'path' },
  { text: '操作', value: 'actions', sortable: false }
];

function showTip(text, color = 'success') {
  snackbar.value.text = text;
  snackbar.value.color = color;
  snackbar.value.show = true;
}

function formatTime(ts) {
  if (!ts) return '-';
  const d = new Date(ts * 1000);
  return d.toLocaleString();
}


async function fetchStatus() {
  try {
    status.value = await props.api.get('plugin/ProxmoxVEBackup/status');
    // 新增：同步镜像模板开关
    if (status.value && typeof status.value.cleanup_template_images !== 'undefined') {
      cleanupTemplateImagesEnabled.value = !!status.value.cleanup_template_images;
    } else {
      // 兼容老后端
      cleanupTemplateImagesEnabled.value = false;
    }
  } catch (e) {
    showTip('获取状态失败: ' + (e?.message || '未知错误'), 'error');
    cleanupTemplateImagesEnabled.value = false;
  }
}

async function fetchHistory() {
  try {
    const [backup, restore] = await Promise.all([
      props.api.get('plugin/ProxmoxVEBackup/backup_history'),
      props.api.get('plugin/ProxmoxVEBackup/restore_history')
    ]);
    // 合并并加类型
    const backupList = Array.isArray(backup) ? backup.map(item => ({ ...item, type: '备份' })) : [];
    const restoreList = Array.isArray(restore) ? restore.map(item => ({ ...item, type: '恢复' })) : [];
    // 合并并按时间倒序
    history.value = [...backupList, ...restoreList].sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
  } catch (e) {
    showTip('获取历史记录失败: ' + (e?.message || '未知错误'), 'error');
  }
}

// fetchPveStatus 成功后写入 localStorage
async function fetchPveStatus() {
  try {
    const data = await props.api.get('plugin/ProxmoxVEBackup/pve_status');
    pveStatus.value = data;
    localStorage.setItem('pveStatus', JSON.stringify(data));
  } catch (e) {
    pveStatus.value = { online: false, error: e?.message || '获取失败' };
  }
}

// fetchContainerStatus 成功后写入 localStorage
async function fetchContainerStatus() {
  try {
    const data = await props.api.get('plugin/ProxmoxVEBackup/container_status');
    containerStatus.value = data;
    localStorage.setItem('containerStatus', JSON.stringify(data));
  } catch (e) {
    containerStatus.value = [{ error: e?.message || '获取失败' }];
  }
}

async function fetchStorages() {
  loadingStorages.value = true;
  try {
    const res = await axios.get('/api/v1/plugin/ProxmoxVEBackup/storages');
    if (res.data && res.data.success && Array.isArray(res.data.storages)) {
      storageOptions.value = res.data.storages.map(s => ({
        label: `${s.name}（${s.type}，可用${s.avail}/总${s.total}）`,
        value: s.name
      }));
      // 默认选第一个
      if (!restoreDisk.value && storageOptions.value.length > 0) {
        restoreDisk.value = storageOptions.value[0].value;
      }
    } else {
      storageOptions.value = [];
    }
  } catch (e) {
    storageOptions.value = [];
  }
  loadingStorages.value = false;
}

async function runBackup() {
  loadingBackup.value = true;
  try {
    const res = await props.api.post('plugin/ProxmoxVEBackup/run_backup');
    if (res.success) {
      showTip(res.message || '备份任务已启动');
    await fetchStatus();
    await fetchHistory();
    } else {
      showTip(res.message || '备份失败', 'error');
    }
  } catch (e) {
    showTip('备份失败: ' + (e?.message || '未知错误'), 'error');
  }
  loadingBackup.value = false;
}

function openRestoreDialog(file) {
  if (file && file.filename && file.source) selectedRestoreFile.value = file.filename;
  else selectedRestoreFile.value = null;
  if (!restoreDisk.value) restoreDisk.value = 'local';
  fetchStorages(); // 打开弹窗时加载存储池
  showRestoreDialog.value = true;
}

async function runRestore() {
  const fileObj = backupFiles.value.find(f => f.filename === selectedRestoreFile.value);
  if (!fileObj || !fileObj.filename || !fileObj.source) {
    return showTip('请选择备份文件', 'error');
  }
  loadingRestore.value = true;
  try {
    const res = await props.api.post('plugin/ProxmoxVEBackup/restore', {
      filename: fileObj.filename,
      source: fileObj.source,
      restore_vmid: restoreVmid.value,
      restore_force: restoreForce.value,
      restore_skip_existing: restoreSkipExisting.value,
      restore_storage: restoreDisk.value
    });
    if (res.success) {
      showTip(res.message || '恢复任务已启动');
      await fetchStatus();
      await fetchHistory();
    } else {
      showTip(res.message || '恢复失败', 'error');
    }
  } catch (e) {
    showTip('恢复失败: ' + (e?.message || '未知错误'), 'error');
  }
  loadingRestore.value = false;
  showRestoreDialog.value = false;
}

async function clearHistory() {
  loadingClear.value = true;
  try {
    await props.api.post('plugin/ProxmoxVEBackup/clear_history');
    showTip('历史已清理');
    await fetchHistory();
  } catch (e) {
    showTip('清理失败: ' + (e?.message || '未知错误'), 'error');
  }
  loadingClear.value = false;
}

function openBackupFilesDialog() {
  fetchBackupFiles();
  showBackupFilesDialog.value = true;
}

async function fetchBackupFiles() {
  try {
    // 直接请求 available_backups 接口，获取备份文件列表
    const files = await props.api.get('plugin/ProxmoxVEBackup/available_backups');
    if (Array.isArray(files)) {
      backupFiles.value = files.map(f => ({
        ...f,
        filenameWithSource: f.filename + '_' + f.source
      }));
    } else {
      backupFiles.value = [];
    }
  } catch (e) {
    backupFiles.value = [];
  }
}

async function downloadBackup(item) {
  // 获取 apikey（假设登录后已存到 localStorage 或 window 变量）
  const apikey = window.API_TOKEN || localStorage.getItem('api_token') || '';
  const params = new URLSearchParams({ filename: item.filename, source: item.source });
  if (apikey) params.append('apikey', apikey); // 新增 apikey
  const url = '/api/v1/plugin/ProxmoxVEBackup/download_backup?' + params.toString();
  try {
    const res = await axios.get(
      url,
      { responseType: 'blob' }
    );
    // 处理文件名
    let filename = item.filename || 'backup.dat';
    const disposition = res.headers['content-disposition'];
    if (disposition) {
      const match = disposition.match(/filename="?([^";]+)"?/);
      if (match) filename = decodeURIComponent(match[1]);
    }
    // 创建blob下载
    const blobUrl = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
  } catch (error) {
    alert('下载失败: ' + (error.message || '未知错误'));
  }
}

function confirmDelete(item) {
  deleteTarget.value = item;
  showDeleteDialog.value = true;
}

async function handleDeleteConfirm() {
  if (!deleteTarget.value) return;
  deleteLoading.value = deleteTarget.value.filename + deleteTarget.value.source;
  try {
    await props.api.post('plugin/ProxmoxVEBackup/delete_backup', {
      filename: deleteTarget.value.filename,
      source: deleteTarget.value.source
    });
    showTip('删除成功');
    await fetchBackupFiles();
  } catch (e) {
    showTip('删除失败: ' + (e?.message || '未知错误'), 'error');
  }
  deleteLoading.value = null;
  showDeleteDialog.value = false;
}


// 体检相关
ref(false);
const showCheckupDialog = ref(false);
const checkupReport = ref({});

// 计算"还有多久"
computed(() => {
  if (!status.value.next_run_time) return '-';
  const now = dayjs();
  const next = dayjs(status.value.next_run_time);
  if (!next.isValid() || next.isBefore(now)) return '-';
  const diff = next.diff(now);
  const d = dayjs.duration(diff);
  let years = Math.floor(d.asYears());
  let days = d.days();
  let hours = d.hours();
  let minutes = d.minutes();
  let parts = [];
  if (years > 0) parts.push(`${years}年`);
  if (days > 0) parts.push(`${days}天`);
  if (hours > 0) parts.push(`${hours}小时`);
  if (minutes > 0) parts.push(`${minutes}分`);
  if (parts.length === 0) parts.push('不到1分钟');
  return parts.join('');
});

// 计算 CRON 表达式描述
computed(() => {
  if (!status.value.cron) return '未配置';
  try {
    return cronstrue.toString(status.value.cron, { locale: 'zh_CN' });
  } catch (e) {
    return '解析失败';
  }
});

// 3. onMounted 时先从 localStorage 读取缓存
onMounted(async () => {
  // 自动获取API_TOKEN
  try {
    const res = await props.api.get('plugin/ProxmoxVEBackup/token');
    if (res && res.api_token) {
      window.API_TOKEN = res.api_token;
      localStorage.setItem('api_token', res.api_token);
    }
  } catch (e) {
    // console.warn('获取API令牌失败', e);
  }
  // 先读缓存
  try {
    const cachePve = localStorage.getItem('pveStatus');
    if (cachePve) pveStatus.value = JSON.parse(cachePve);
  } catch {}
  try {
    const cacheContainer = localStorage.getItem('containerStatus');
    if (cacheContainer) containerStatus.value = JSON.parse(cacheContainer);
  } catch {}
  // 再异步刷新
  fetchStatus();
  fetchHistory();
  fetchPveStatus();
  setInterval(fetchStatus, 30000); // 30秒轮询状态
  setInterval(fetchPveStatus, 60000); // 60秒轮询PVE状态
  fetchContainerStatus();
  setInterval(fetchContainerStatus, 120000); // 120秒轮询容器状态
  fetchBackupFiles();
});

async function handleVmAction(item, action) {
  item._actionLoading = action;
  try {
    const res = await props.api.post('plugin/ProxmoxVEBackup/container_action', {
      vmid: item.vmid,
      type: item.type,
      action
    });
    showTip(res.message || (action + '操作完成'), res.success ? 'success' : 'error');
    await fetchContainerStatus();
  } catch (e) {
    showTip('操作失败: ' + (e?.message || '未知错误'), 'error');
  }
  item._actionLoading = null;
}

async function handleVmSnapshot(item) {
  item._actionLoading = 'snapshot';
  try {
    const res = await props.api.post('plugin/ProxmoxVEBackup/container_snapshot', {
      vmid: item.vmid,
      type: item.type
    });
    showTip(res.message || '快照操作完成', res.success ? 'success' : 'error');
    await fetchContainerStatus();
  } catch (e) {
    showTip('快照失败: ' + (e?.message || '未知错误'), 'error');
  }
  item._actionLoading = null;
}

function formatUptime(uptime) {
  const sec = Number(uptime);
  if (!sec || isNaN(sec) || sec <= 0) return '<span style="color:#888;">未运行</span>';
  if (sec < 60) return '<span style="color:#4caf50;font-weight:600;">刚启动</span>';
  const days = Math.floor(sec / 86400);
  const hours = Math.floor((sec % 86400) / 3600);
  const mins = Math.floor((sec % 3600) / 60);
  let parts = [];
  if (days > 0) parts.push(days + '天');
  if (hours > 0) parts.push(hours + '小时');
  if (mins > 0) parts.push(mins + '分');
  return `<span style="color:#4caf50;font-weight:600;">运行${parts.join('')}</span>`;
}

const isMobile = ref(false);
onMounted(() => {
  const check = () => isMobile.value = window.innerWidth < 600;
  check();
  window.addEventListener('resize', check);
});

// 辅助函数：获取使用率颜色
function getUsageColor(usage) {
  if (usage >= 80) return 'error';
  if (usage >= 50) return 'warning';
  return 'success';
}

// 辅助函数：获取磁盘使用率颜色
function getDiskUsageColor(usage) {
  if (usage >= 90) return 'error';
  if (usage >= 70) return 'warning';
  return 'success';
}

// 辅助函数：获取温度颜色
function getTempColor(temp) {
  if (temp >= 80) return 'error';
  if (temp >= 60) return 'warning';
  return 'success';
}

// 辅助函数：获取温度颜色的实际值（用于内联样式）
function getTempColorValue(temp) {
  if (temp >= 80) return '#f44336'; // 红色 - 高温
  if (temp >= 60) return '#ff9800'; // 橙色 - 警告
  return '#4caf50'; // 绿色 - 正常
}

// 辅助函数：格式化IO延迟
function formatIODelay(delay) {
  if (!delay && delay !== 0) return '-';
  if (delay < 1) return '< 1ms';
  return `${delay.toFixed(1)}ms`;
}

// 辅助函数：获取IO延迟颜色
function getIODelayColor(delay) {
  if (delay >= 50) return 'error'; // 红色 - 严重延迟
  if (delay >= 10) return 'warning'; // 橙色 - 警告
  return 'success'; // 绿色 - 正常
}

// 辅助函数：获取IO延迟进度条值（将毫秒映射到0-100）
function getIODelayProgress(delay) {
  // 将0-100ms映射到0-100%，超过100ms显示为100%
  return Math.min((delay / 100) * 100, 100);
}

const showHostActionDialog = ref(false);
const pendingHostAction = ref(''); // reboot/shutdown
const hostActionLoading = ref('');
const handleHostActionClick = (action) => {
  if (hostActionLoading.value) return;
  pendingHostAction.value = action;
  showHostActionDialog.value = true;
};
const doHostAction = async () => {
  const action = pendingHostAction.value;
  if (!action) return;
  hostActionLoading.value = action;
  try {
    const actionText = action === 'reboot' ? '重启' : '关机';
    const res = await props.api.post('plugin/ProxmoxVEBackup/host_action', { action });
    if (res.success) {
      showTip(res.msg || `${actionText}命令已发送`);
      setTimeout(fetchPveStatus, 2000);
    } else {
      showTip(res.msg || `${actionText}失败`);
    }
  } catch (e) {
    showTip(e.message || '操作失败');
  }
  hostActionLoading.value = '';
  showHostActionDialog.value = false;
  pendingHostAction.value = '';
};

const loadingCleanupLogs = ref(false);
const loadingCleanupTempSpace = ref(false); // 新增临时空间清理loading
async function handleCleanupLogs() {
  if (!status.value.enabled || !status.value.enable_log_cleanup) return;
  loadingCleanupLogs.value = true;
  try {
    const res = await props.api.post('plugin/ProxmoxVEBackup/cleanup_logs');
    let detail = '';
    if (res.result && typeof res.result === 'object') {
      detail = Object.entries(res.result).map(([k, v]) => {
        const [count, err] = v;
        if (err) return `${k}：失败（${err}）`;
        if (count === null || typeof count === 'undefined') return `${k}：已清理`;
        return `${k}：已清理${count}个`;
      }).join('\n');
    }
    showTip((res.msg || '系统日志清理完成') + (detail ? '\n' + detail : ''), res.success ? 'success' : 'error');
  } catch (e) {
    showTip(e?.msg || e?.message || '系统日志清理失败', 'error');
  }
  loadingCleanupLogs.value = false;
}

// 新增：清理临时空间方法
async function handleCleanupTempSpace() {
  if (!status.value.enabled) return;
  if (status.value.backup_activity && status.value.backup_activity !== '空闲') {
    showTip('当前有备份任务进行中，请稍后再清理临时空间', 'warning');
    return;
  }
  loadingCleanupTempSpace.value = true;
  try {
    const res = await props.api.post('plugin/ProxmoxVEBackup/cleanup_tmp');
    let detail = '';
    if (res.result && typeof res.result === 'object') {
      detail = Object.entries(res.result).map(([k, v]) => {
        const [count, err] = v;
        if (err) return `${k}：失败（${err}）`;
        if (count === null || typeof count === 'undefined') return `${k}：已清理`;
        return `${k}：已清理${count}个`;
      }).join('\n');
    }
    showTip((res.msg || '临时空间清理完成') + (detail ? '\n' + detail : ''), res.success ? 'success' : 'error');
  } catch (e) {
    showTip(e?.msg || e?.message || '临时空间清理失败', 'error');
  }
  loadingCleanupTempSpace.value = false;
}

// 新增：停止所有任务方法
async function stopAllTasks() {
  loadingStopTasks.value = true;
  try {
    const res = await props.api.post('plugin/ProxmoxVEBackup/stop_all_tasks');
    showTip(res.msg || '任务已停止', res.success ? 'success' : 'error');
    if (res.success) {
      await fetchStatus(); // 刷新状态
    }
  } catch (e) {
    showTip(e?.msg || e?.message || '停止任务失败', 'error');
  }
  loadingStopTasks.value = false;
}

const cleanupTemplateImagesEnabled = ref(false); // 镜像模板开关联动
const showTemplateImagesDialog = ref(false);
const templateImages = ref([]);
const templateImageHeaders = [
  { text: '文件名', value: 'filename' },
  { text: '类型', value: 'type' },
  { text: '大小(MB)', value: 'size_mb' },
  { text: '日期', value: 'date' }
  // 不再有操作列
];
function openTemplateImagesDialog() {
  fetchTemplateImages();
  showTemplateImagesDialog.value = true;
}
async function fetchTemplateImages() {
  try {
    const files = await props.api.get('plugin/ProxmoxVEBackup/template_images');
    if (Array.isArray(files)) {
      templateImages.value = files.map(f => ({
        ...f,
        filenameWithType: f.filename + '_' + f.type
      }));
    } else {
      templateImages.value = [];
    }
  } catch (e) {
    templateImages.value = [];
  }
}

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_spacer = _resolveComponent("v-spacer");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_card_title = _resolveComponent("v-card-title");
  const _component_v_tooltip = _resolveComponent("v-tooltip");
  const _component_v_progress_linear = _resolveComponent("v-progress-linear");
  const _component_v_card = _resolveComponent("v-card");
  const _component_v_col = _resolveComponent("v-col");
  const _component_v_row = _resolveComponent("v-row");
  const _component_v_chip = _resolveComponent("v-chip");
  const _component_v_data_table = _resolveComponent("v-data-table");
  const _component_v_select = _resolveComponent("v-select");
  const _component_v_text_field = _resolveComponent("v-text-field");
  const _component_v_switch = _resolveComponent("v-switch");
  const _component_v_card_text = _resolveComponent("v-card-text");
  const _component_v_card_actions = _resolveComponent("v-card-actions");
  const _component_v_dialog = _resolveComponent("v-dialog");
  const _component_v_snackbar = _resolveComponent("v-snackbar");
  const _component_v_list_item_title = _resolveComponent("v-list-item-title");
  const _component_v_list_item_subtitle = _resolveComponent("v-list-item-subtitle");
  const _component_v_list_item_content = _resolveComponent("v-list-item-content");
  const _component_v_list_item = _resolveComponent("v-list-item");
  const _component_v_list = _resolveComponent("v-list");

  return (_openBlock(), _createElementBlock(_Fragment, null, [
    _createVNode(_component_v_card, {
      flat: "",
      class: "plugin-page glass-card"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card_title, {
          class: "section-title d-flex align-center mb-1",
          style: {"padding":"10px 0 6px 0","min-height":"unset"}
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_icon, {
              class: "mr-1",
              color: "primary",
              size: "26"
            }, {
              default: _withCtx(() => _cache[27] || (_cache[27] = [
                _createTextVNode("mdi-server")
              ])),
              _: 1
            }),
            _cache[29] || (_cache[29] = _createElementVNode("span", { style: {"font-size":"1.15rem","font-weight":"600","letter-spacing":"1px"} }, "PVE虚拟机守护神", -1)),
            _createVNode(_component_v_spacer),
            (isMobile.value)
              ? (_openBlock(), _createBlock(_component_v_btn, {
                  key: 0,
                  icon: "",
                  class: "close-btn",
                  onClick: _cache[0] || (_cache[0] = $event => (_ctx.$emit('close'))),
                  style: {"margin-left":"auto","background":"transparent","box-shadow":"none","min-width":"unset","width":"auto","height":"auto"}
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_icon, {
                      size: "28",
                      style: {"color":"#999"}
                    }, {
                      default: _withCtx(() => _cache[28] || (_cache[28] = [
                        _createTextVNode("mdi-close")
                      ])),
                      _: 1
                    })
                  ]),
                  _: 1
                }))
              : _createCommentVNode("", true)
          ]),
          _: 1
        }),
        _createElementVNode("div", _hoisted_1, [
          _createVNode(_component_v_row, { class: "status-main-row" }, {
            default: _withCtx(() => [
              _createVNode(_component_v_col, {
                cols: "12",
                class: "status-col"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_card, {
                    class: "modern-status-card",
                    elevation: "0"
                  }, {
                    default: _withCtx(() => [
                      _createElementVNode("div", _hoisted_2, [
                        _createElementVNode("div", _hoisted_3, [
                          _createElementVNode("div", _hoisted_4, [
                            _createVNode(_component_v_icon, {
                              size: "24",
                              color: "success"
                            }, {
                              default: _withCtx(() => _cache[30] || (_cache[30] = [
                                _createTextVNode("mdi-server")
                              ])),
                              _: 1
                            })
                          ]),
                          _cache[31] || (_cache[31] = _createElementVNode("div", null, [
                            _createElementVNode("div", { class: "card-title-modern" }, "PVE主机状态"),
                            _createElementVNode("div", { class: "card-subtitle-modern" }, "Host Status")
                          ], -1))
                        ]),
                        _createElementVNode("div", _hoisted_5, [
                          _createElementVNode("div", _hoisted_6, [
                            _createVNode(_component_v_icon, {
                              size: "16",
                              color: "primary",
                              class: "mr-1"
                            }, {
                              default: _withCtx(() => _cache[32] || (_cache[32] = [
                                _createTextVNode("mdi-server-network")
                              ])),
                              _: 1
                            }),
                            _cache[33] || (_cache[33] = _createElementVNode("span", { class: "pve-header-label" }, "主机名", -1)),
                            _createElementVNode("span", _hoisted_7, _toDisplayString(pveStatus.value.hostname || '-'), 1)
                          ]),
                          _createElementVNode("div", _hoisted_8, [
                            _createVNode(_component_v_icon, {
                              size: "16",
                              color: "cyan",
                              class: "mr-1"
                            }, {
                              default: _withCtx(() => _cache[34] || (_cache[34] = [
                                _createTextVNode("mdi-ip-network")
                              ])),
                              _: 1
                            }),
                            _cache[35] || (_cache[35] = _createElementVNode("span", { class: "pve-header-label" }, "主机IP", -1)),
                            _createElementVNode("span", _hoisted_9, _toDisplayString(pveStatus.value.ip || '-'), 1)
                          ]),
                          _createElementVNode("div", _hoisted_10, [
                            _createVNode(_component_v_icon, {
                              size: "16",
                              color: "cyan",
                              class: "mr-1"
                            }, {
                              default: _withCtx(() => _cache[36] || (_cache[36] = [
                                _createTextVNode("mdi-chart-line")
                              ])),
                              _: 1
                            }),
                            _cache[37] || (_cache[37] = _createElementVNode("span", { class: "pve-header-label" }, "负载", -1)),
                            _createElementVNode("span", _hoisted_11, _toDisplayString(pveStatus.value.load_avg?.join(' / ') || '-'), 1)
                          ]),
                          _createElementVNode("div", _hoisted_12, [
                            _createVNode(_component_v_icon, {
                              size: "16",
                              color: "grey",
                              class: "mr-1"
                            }, {
                              default: _withCtx(() => _cache[38] || (_cache[38] = [
                                _createTextVNode("mdi-cog")
                              ])),
                              _: 1
                            }),
                            _cache[39] || (_cache[39] = _createElementVNode("span", { class: "pve-header-label" }, "内核", -1)),
                            _createElementVNode("span", _hoisted_13, _toDisplayString(pveStatus.value.kernel || '-'), 1)
                          ]),
                          (pveStatus.value.pve_version)
                            ? (_openBlock(), _createElementBlock("div", _hoisted_14, [
                                _createVNode(_component_v_icon, {
                                  size: "16",
                                  color: "blue",
                                  class: "mr-1"
                                }, {
                                  default: _withCtx(() => _cache[40] || (_cache[40] = [
                                    _createTextVNode("mdi-tag")
                                  ])),
                                  _: 1
                                }),
                                _cache[41] || (_cache[41] = _createElementVNode("span", { class: "pve-header-label" }, "PVE版本", -1)),
                                _createElementVNode("span", _hoisted_15, _toDisplayString(pveStatus.value.pve_version), 1)
                              ]))
                            : _createCommentVNode("", true)
                        ]),
                        _createElementVNode("div", _hoisted_16, [
                          _createVNode(_component_v_tooltip, {
                            text: "刷新状态",
                            location: "bottom"
                          }, {
                            activator: _withCtx(({ props }) => [
                              _createVNode(_component_v_btn, _mergeProps({ icon: "" }, props, {
                                class: "modern-action-btn refresh-btn",
                                onClick: fetchPveStatus,
                                size: "small"
                              }), {
                                default: _withCtx(() => [
                                  _createVNode(_component_v_icon, { size: "20" }, {
                                    default: _withCtx(() => _cache[42] || (_cache[42] = [
                                      _createTextVNode("mdi-refresh")
                                    ])),
                                    _: 1
                                  })
                                ]),
                                _: 2
                              }, 1040)
                            ]),
                            _: 1
                          }),
                          _createVNode(_component_v_tooltip, {
                            text: "重启主机",
                            location: "bottom"
                          }, {
                            activator: _withCtx(({ props }) => [
                              _createVNode(_component_v_btn, _mergeProps({ icon: "" }, props, {
                                class: "modern-action-btn reboot-btn",
                                loading: hostActionLoading.value === 'reboot',
                                onClick: _cache[1] || (_cache[1] = $event => (handleHostActionClick('reboot'))),
                                size: "small"
                              }), {
                                default: _withCtx(() => [
                                  _createVNode(_component_v_icon, { size: "20" }, {
                                    default: _withCtx(() => _cache[43] || (_cache[43] = [
                                      _createTextVNode("mdi-restart")
                                    ])),
                                    _: 1
                                  })
                                ]),
                                _: 2
                              }, 1040, ["loading"])
                            ]),
                            _: 1
                          }),
                          _createVNode(_component_v_tooltip, {
                            text: "关闭主机",
                            location: "bottom"
                          }, {
                            activator: _withCtx(({ props }) => [
                              _createVNode(_component_v_btn, _mergeProps({ icon: "" }, props, {
                                class: "modern-action-btn shutdown-btn",
                                loading: hostActionLoading.value === 'shutdown',
                                onClick: _cache[2] || (_cache[2] = $event => (handleHostActionClick('shutdown'))),
                                size: "small"
                              }), {
                                default: _withCtx(() => [
                                  _createVNode(_component_v_icon, { size: "20" }, {
                                    default: _withCtx(() => _cache[44] || (_cache[44] = [
                                      _createTextVNode("mdi-power")
                                    ])),
                                    _: 1
                                  })
                                ]),
                                _: 2
                              }, 1040, ["loading"])
                            ]),
                            _: 1
                          })
                        ])
                      ]),
                      _createElementVNode("div", _hoisted_17, [
                        (pveStatus.value.online)
                          ? (_openBlock(), _createElementBlock("div", _hoisted_18, [
                              _createElementVNode("div", _hoisted_19, [
                                _createElementVNode("div", _hoisted_20, [
                                  _createElementVNode("div", _hoisted_21, [
                                    _createVNode(_component_v_icon, {
                                      size: "16",
                                      color: "info",
                                      class: "mr-2"
                                    }, {
                                      default: _withCtx(() => _cache[45] || (_cache[45] = [
                                        _createTextVNode("mdi-chip")
                                      ])),
                                      _: 1
                                    }),
                                    _cache[46] || (_cache[46] = _createElementVNode("span", { class: "status-label" }, "CPU", -1))
                                  ]),
                                  _createElementVNode("div", _hoisted_22, [
                                    _createElementVNode("div", _hoisted_23, [
                                      _createElementVNode("span", _hoisted_24, _toDisplayString(pveStatus.value.cpu_cores) + "核", 1),
                                      (pveStatus.value.cpu_temp)
                                        ? (_openBlock(), _createElementBlock("span", {
                                            key: 0,
                                            class: _normalizeClass(["resource-temp-inline", `temp-${getTempColor(pveStatus.value.cpu_temp)}`])
                                          }, [
                                            _createVNode(_component_v_icon, {
                                              size: "12",
                                              class: "mr-1",
                                              color: getTempColor(pveStatus.value.cpu_temp)
                                            }, {
                                              default: _withCtx(() => _cache[47] || (_cache[47] = [
                                                _createTextVNode("mdi-thermometer")
                                              ])),
                                              _: 1
                                            }, 8, ["color"]),
                                            _createElementVNode("span", {
                                              style: _normalizeStyle({ color: getTempColorValue(pveStatus.value.cpu_temp) })
                                            }, _toDisplayString(pveStatus.value.cpu_temp) + "°C", 5)
                                          ], 2))
                                        : _createCommentVNode("", true)
                                    ]),
                                    _createElementVNode("div", _hoisted_25, [
                                      _createVNode(_component_v_progress_linear, {
                                        "model-value": pveStatus.value.cpu_usage || 0,
                                        color: getUsageColor(pveStatus.value.cpu_usage || 0),
                                        height: "6",
                                        rounded: "",
                                        class: "resource-progress"
                                      }, null, 8, ["model-value", "color"]),
                                      _createElementVNode("span", _hoisted_26, _toDisplayString(pveStatus.value.cpu_usage) + "%", 1)
                                    ])
                                  ])
                                ]),
                                _createElementVNode("div", _hoisted_27, [
                                  _createElementVNode("div", _hoisted_28, [
                                    _createVNode(_component_v_icon, {
                                      size: "16",
                                      color: "purple",
                                      class: "mr-2"
                                    }, {
                                      default: _withCtx(() => _cache[48] || (_cache[48] = [
                                        _createTextVNode("mdi-memory")
                                      ])),
                                      _: 1
                                    }),
                                    _cache[49] || (_cache[49] = _createElementVNode("span", { class: "status-label" }, "内存", -1))
                                  ]),
                                  _createElementVNode("div", _hoisted_29, [
                                    _createElementVNode("div", _hoisted_30, [
                                      _createElementVNode("span", _hoisted_31, _toDisplayString(pveStatus.value.mem_used) + "/" + _toDisplayString(pveStatus.value.mem_total) + "MB", 1)
                                    ]),
                                    _createElementVNode("div", _hoisted_32, [
                                      _createVNode(_component_v_progress_linear, {
                                        "model-value": pveStatus.value.mem_usage || 0,
                                        color: getUsageColor(pveStatus.value.mem_usage || 0),
                                        height: "6",
                                        rounded: "",
                                        class: "resource-progress"
                                      }, null, 8, ["model-value", "color"]),
                                      _createElementVNode("span", _hoisted_33, _toDisplayString(pveStatus.value.mem_usage) + "%", 1)
                                    ])
                                  ])
                                ]),
                                _createElementVNode("div", _hoisted_34, [
                                  _createElementVNode("div", _hoisted_35, [
                                    _createVNode(_component_v_icon, {
                                      size: "16",
                                      color: "orange",
                                      class: "mr-2"
                                    }, {
                                      default: _withCtx(() => _cache[50] || (_cache[50] = [
                                        _createTextVNode("mdi-harddisk")
                                      ])),
                                      _: 1
                                    }),
                                    _cache[51] || (_cache[51] = _createElementVNode("span", { class: "status-label" }, "硬盘", -1))
                                  ]),
                                  _createElementVNode("div", _hoisted_36, [
                                    _createElementVNode("div", _hoisted_37, [
                                      _createElementVNode("span", _hoisted_38, _toDisplayString(pveStatus.value.disk_used) + "/" + _toDisplayString(pveStatus.value.disk_total) + "MB", 1),
                                      (pveStatus.value.disk_temp)
                                        ? (_openBlock(), _createElementBlock("span", {
                                            key: 0,
                                            class: _normalizeClass(["resource-temp-inline", `temp-${getTempColor(pveStatus.value.disk_temp)}`])
                                          }, [
                                            _createVNode(_component_v_icon, {
                                              size: "12",
                                              class: "mr-1",
                                              color: getTempColor(pveStatus.value.disk_temp)
                                            }, {
                                              default: _withCtx(() => _cache[52] || (_cache[52] = [
                                                _createTextVNode("mdi-thermometer")
                                              ])),
                                              _: 1
                                            }, 8, ["color"]),
                                            _createElementVNode("span", {
                                              style: _normalizeStyle({ color: getTempColorValue(pveStatus.value.disk_temp) })
                                            }, _toDisplayString(pveStatus.value.disk_temp) + "°C", 5)
                                          ], 2))
                                        : _createCommentVNode("", true)
                                    ]),
                                    _createElementVNode("div", _hoisted_39, [
                                      _createVNode(_component_v_progress_linear, {
                                        "model-value": pveStatus.value.disk_usage || 0,
                                        color: getDiskUsageColor(pveStatus.value.disk_usage || 0),
                                        height: "6",
                                        rounded: "",
                                        class: "resource-progress"
                                      }, null, 8, ["model-value", "color"]),
                                      _createElementVNode("span", _hoisted_40, _toDisplayString(pveStatus.value.disk_usage) + "%", 1)
                                    ])
                                  ])
                                ]),
                                (pveStatus.value.swap_total)
                                  ? (_openBlock(), _createElementBlock("div", _hoisted_41, [
                                      _createElementVNode("div", _hoisted_42, [
                                        _createVNode(_component_v_icon, {
                                          size: "16",
                                          color: "purple",
                                          class: "mr-2"
                                        }, {
                                          default: _withCtx(() => _cache[53] || (_cache[53] = [
                                            _createTextVNode("mdi-swap-horizontal")
                                          ])),
                                          _: 1
                                        }),
                                        _cache[54] || (_cache[54] = _createElementVNode("span", { class: "status-label" }, "SWAP", -1))
                                      ]),
                                      _createElementVNode("div", _hoisted_43, [
                                        _createElementVNode("div", _hoisted_44, [
                                          _createElementVNode("span", _hoisted_45, _toDisplayString(pveStatus.value.swap_used || 0) + "/" + _toDisplayString(pveStatus.value.swap_total) + "MB", 1)
                                        ]),
                                        _createElementVNode("div", _hoisted_46, [
                                          _createVNode(_component_v_progress_linear, {
                                            "model-value": pveStatus.value.swap_usage || 0,
                                            color: getUsageColor(pveStatus.value.swap_usage || 0),
                                            height: "6",
                                            rounded: "",
                                            class: "resource-progress"
                                          }, null, 8, ["model-value", "color"]),
                                          _createElementVNode("span", _hoisted_47, _toDisplayString(pveStatus.value.swap_usage ? pveStatus.value.swap_usage.toFixed(1) : 0) + "%", 1)
                                        ])
                                      ])
                                    ]))
                                  : _createCommentVNode("", true),
                                (pveStatus.value.io_delay !== undefined && pveStatus.value.io_delay !== null)
                                  ? (_openBlock(), _createElementBlock("div", _hoisted_48, [
                                      _createElementVNode("div", _hoisted_49, [
                                        _createVNode(_component_v_icon, {
                                          size: "16",
                                          color: "red",
                                          class: "mr-2"
                                        }, {
                                          default: _withCtx(() => _cache[55] || (_cache[55] = [
                                            _createTextVNode("mdi-clock-outline")
                                          ])),
                                          _: 1
                                        }),
                                        _cache[56] || (_cache[56] = _createElementVNode("span", { class: "status-label" }, "IO延迟", -1))
                                      ]),
                                      _createElementVNode("div", _hoisted_50, [
                                        _createElementVNode("div", _hoisted_51, [
                                          _createElementVNode("span", _hoisted_52, _toDisplayString(formatIODelay(pveStatus.value.io_delay)), 1)
                                        ]),
                                        _createElementVNode("div", _hoisted_53, [
                                          _createVNode(_component_v_progress_linear, {
                                            "model-value": getIODelayProgress(pveStatus.value.io_delay || 0),
                                            color: getIODelayColor(pveStatus.value.io_delay || 0),
                                            height: "6",
                                            rounded: "",
                                            class: "resource-progress"
                                          }, null, 8, ["model-value", "color"]),
                                          _createElementVNode("span", _hoisted_54, _toDisplayString(formatIODelay(pveStatus.value.io_delay)), 1)
                                        ])
                                      ])
                                    ]))
                                  : _createCommentVNode("", true)
                              ])
                            ]))
                          : (_openBlock(), _createElementBlock("div", _hoisted_55, [
                              _createVNode(_component_v_icon, {
                                size: "56",
                                color: "error",
                                class: "mb-3"
                              }, {
                                default: _withCtx(() => _cache[57] || (_cache[57] = [
                                  _createTextVNode("mdi-alert-circle-outline")
                                ])),
                                _: 1
                              }),
                              _cache[58] || (_cache[58] = _createElementVNode("div", { class: "offline-text" }, "主机离线或连接失败", -1)),
                              _createElementVNode("div", _hoisted_56, _toDisplayString(pveStatus.value.error), 1)
                            ]))
                      ])
                    ]),
                    _: 1
                  })
                ]),
                _: 1
              })
            ]),
            _: 1
          }),
          _createVNode(_component_v_row, { class: "status-main-row" }, {
            default: _withCtx(() => [
              _createVNode(_component_v_col, {
                cols: "12",
                class: "status-col"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_v_card, {
                    class: "modern-status-card",
                    elevation: "0"
                  }, {
                    default: _withCtx(() => [
                      _createElementVNode("div", _hoisted_57, [
                        _createElementVNode("div", _hoisted_58, [
                          _createElementVNode("div", _hoisted_59, [
                            _createVNode(_component_v_icon, {
                              size: "24",
                              color: "info"
                            }, {
                              default: _withCtx(() => _cache[59] || (_cache[59] = [
                                _createTextVNode("mdi-docker")
                              ])),
                              _: 1
                            })
                          ]),
                          _cache[60] || (_cache[60] = _createElementVNode("div", null, [
                            _createElementVNode("div", { class: "card-title-modern" }, "容器状态"),
                            _createElementVNode("div", { class: "card-subtitle-modern" }, "Container Status")
                          ], -1))
                        ]),
                        _createElementVNode("div", _hoisted_60, [
                          _createElementVNode("div", _hoisted_61, [
                            _createVNode(_component_v_icon, {
                              size: "18",
                              color: "primary",
                              class: "mr-2"
                            }, {
                              default: _withCtx(() => _cache[61] || (_cache[61] = [
                                _createTextVNode("mdi-docker")
                              ])),
                              _: 1
                            }),
                            _cache[62] || (_cache[62] = _createElementVNode("span", { class: "header-summary-label" }, "容器总数", -1)),
                            _createVNode(_component_v_chip, {
                              size: "x-small",
                              color: "primary",
                              class: "ml-2"
                            }, {
                              default: _withCtx(() => [
                                _createTextVNode(_toDisplayString(containerStatus.value.length), 1)
                              ]),
                              _: 1
                            })
                          ]),
                          _createElementVNode("div", _hoisted_62, [
                            _createVNode(_component_v_icon, {
                              size: "18",
                              color: "purple",
                              class: "mr-2"
                            }, {
                              default: _withCtx(() => _cache[63] || (_cache[63] = [
                                _createTextVNode("mdi-server")
                              ])),
                              _: 1
                            }),
                            _cache[64] || (_cache[64] = _createElementVNode("span", { class: "header-summary-label" }, "QEMU", -1)),
                            _createVNode(_component_v_chip, {
                              size: "x-small",
                              color: "purple",
                              class: "ml-2"
                            }, {
                              default: _withCtx(() => [
                                _createTextVNode(_toDisplayString(containerStatus.value.filter(c => c.type === 'qemu').length), 1)
                              ]),
                              _: 1
                            })
                          ]),
                          _createElementVNode("div", _hoisted_63, [
                            _createVNode(_component_v_icon, {
                              size: "18",
                              color: "info",
                              class: "mr-2"
                            }, {
                              default: _withCtx(() => _cache[65] || (_cache[65] = [
                                _createTextVNode("mdi-cube-outline")
                              ])),
                              _: 1
                            }),
                            _cache[66] || (_cache[66] = _createElementVNode("span", { class: "header-summary-label" }, "LXC", -1)),
                            _createVNode(_component_v_chip, {
                              size: "x-small",
                              color: "info",
                              class: "ml-2"
                            }, {
                              default: _withCtx(() => [
                                _createTextVNode(_toDisplayString(containerStatus.value.filter(c => c.type === 'lxc').length), 1)
                              ]),
                              _: 1
                            })
                          ]),
                          _createElementVNode("div", _hoisted_64, [
                            _createVNode(_component_v_icon, {
                              size: "18",
                              color: "success",
                              class: "mr-2"
                            }, {
                              default: _withCtx(() => _cache[67] || (_cache[67] = [
                                _createTextVNode("mdi-play-circle")
                              ])),
                              _: 1
                            }),
                            _cache[68] || (_cache[68] = _createElementVNode("span", { class: "header-summary-label" }, "运行中", -1)),
                            _createVNode(_component_v_chip, {
                              size: "x-small",
                              color: "success",
                              class: "ml-2"
                            }, {
                              default: _withCtx(() => [
                                _createTextVNode(_toDisplayString(containerStatus.value.filter(c => c.status === 'running').length), 1)
                              ]),
                              _: 1
                            })
                          ]),
                          _createElementVNode("div", _hoisted_65, [
                            _createVNode(_component_v_icon, {
                              size: "18",
                              color: "grey",
                              class: "mr-2"
                            }, {
                              default: _withCtx(() => _cache[69] || (_cache[69] = [
                                _createTextVNode("mdi-stop-circle")
                              ])),
                              _: 1
                            }),
                            _cache[70] || (_cache[70] = _createElementVNode("span", { class: "header-summary-label" }, "已停止", -1)),
                            _createVNode(_component_v_chip, {
                              size: "x-small",
                              color: "grey",
                              class: "ml-2"
                            }, {
                              default: _withCtx(() => [
                                _createTextVNode(_toDisplayString(containerStatus.value.filter(c => c.status !== 'running').length), 1)
                              ]),
                              _: 1
                            })
                          ])
                        ]),
                        _createVNode(_component_v_tooltip, {
                          text: "刷新容器状态",
                          location: "bottom"
                        }, {
                          activator: _withCtx(({ props }) => [
                            _createVNode(_component_v_btn, _mergeProps({ icon: "" }, props, {
                              class: "modern-action-btn refresh-btn",
                              onClick: fetchContainerStatus,
                              size: "small"
                            }), {
                              default: _withCtx(() => [
                                _createVNode(_component_v_icon, {
                                  icon: "mdi-sync",
                                  size: "20"
                                })
                              ]),
                              _: 2
                            }, 1040)
                          ]),
                          _: 1
                        })
                      ]),
                      _createElementVNode("div", _hoisted_66, [
                        (!isMobile.value)
                          ? (_openBlock(), _createElementBlock("div", _hoisted_67, [
                              _createVNode(_component_v_data_table, {
                                headers: containerHeaders,
                                items: containerStatus.value,
                                class: "elevation-0",
                                "hide-default-footer": "",
                                density: "compact"
                              }, {
                                "item.type": _withCtx(({ item }) => [
                                  _createVNode(_component_v_chip, {
                                    size: "x-small",
                                    color: item.type === 'qemu' ? 'primary' : 'info'
                                  }, {
                                    default: _withCtx(() => [
                                      _createTextVNode(_toDisplayString(item.type === 'qemu' ? 'QEMU' : (item.type === 'lxc' ? 'LXC' : item.type)), 1)
                                    ]),
                                    _: 2
                                  }, 1032, ["color"])
                                ]),
                                "item.status": _withCtx(({ item }) => [
                                  _createVNode(_component_v_chip, {
                                    color: item.status === 'running' ? 'success' : 'grey',
                                    size: "x-small"
                                  }, {
                                    default: _withCtx(() => [
                                      _createTextVNode(_toDisplayString(item.status), 1)
                                    ]),
                                    _: 2
                                  }, 1032, ["color"])
                                ]),
                                "item.tags": _withCtx(({ item }) => [
                                  (!item.tags || !item.tags.trim())
                                    ? (_openBlock(), _createElementBlock("span", _hoisted_68, "-"))
                                    : (_openBlock(true), _createElementBlock(_Fragment, { key: 1 }, _renderList(item.tags.split(/[,;]+/).map(t => t.trim()).filter(Boolean), (tag) => {
                                        return (_openBlock(), _createBlock(_component_v_chip, {
                                          key: tag,
                                          size: "x-small",
                                          style: _normalizeStyle({ backgroundColor: getPveTagColor(tag), color: '#fff', fontWeight: 600 }),
                                          class: "mr-1"
                                        }, {
                                          default: _withCtx(() => [
                                            _createTextVNode(_toDisplayString(tag), 1)
                                          ]),
                                          _: 2
                                        }, 1032, ["style"]))
                                      }), 128))
                                ]),
                                "item.uptime": _withCtx(({ item }) => [
                                  _createElementVNode("span", {
                                    innerHTML: formatUptime(item.uptime)
                                  }, null, 8, _hoisted_69)
                                ]),
                                "item.actions": _withCtx(({ item }) => [
                                  _createElementVNode("div", _hoisted_70, [
                                    _createVNode(_component_v_btn, {
                                      size: "x-small",
                                      color: "success",
                                      loading: item._actionLoading === 'start',
                                      disabled: item.status === 'running',
                                      onClick: $event => (handleVmAction(item, 'start')),
                                      class: "mr-1"
                                    }, {
                                      default: _withCtx(() => _cache[71] || (_cache[71] = [
                                        _createTextVNode("启动")
                                      ])),
                                      _: 2
                                    }, 1032, ["loading", "disabled", "onClick"]),
                                    _createVNode(_component_v_btn, {
                                      size: "x-small",
                                      color: "error",
                                      loading: item._actionLoading === 'stop',
                                      disabled: item.status !== 'running',
                                      onClick: $event => (handleVmAction(item, 'stop')),
                                      class: "mr-1"
                                    }, {
                                      default: _withCtx(() => _cache[72] || (_cache[72] = [
                                        _createTextVNode("关闭")
                                      ])),
                                      _: 2
                                    }, 1032, ["loading", "disabled", "onClick"]),
                                    _createVNode(_component_v_btn, {
                                      size: "x-small",
                                      color: "info",
                                      loading: item._actionLoading === 'reboot',
                                      disabled: item.status !== 'running',
                                      onClick: $event => (handleVmAction(item, 'reboot')),
                                      class: "mr-1"
                                    }, {
                                      default: _withCtx(() => _cache[73] || (_cache[73] = [
                                        _createTextVNode("重启")
                                      ])),
                                      _: 2
                                    }, 1032, ["loading", "disabled", "onClick"]),
                                    _createVNode(_component_v_btn, {
                                      size: "x-small",
                                      color: "primary",
                                      loading: item._actionLoading === 'snapshot',
                                      onClick: $event => (handleVmSnapshot(item))
                                    }, {
                                      default: _withCtx(() => _cache[74] || (_cache[74] = [
                                        _createTextVNode("创建快照")
                                      ])),
                                      _: 2
                                    }, 1032, ["loading", "onClick"])
                                  ])
                                ]),
                                _: 1
                              }, 8, ["items"])
                            ]))
                          : (_openBlock(), _createElementBlock("div", _hoisted_71, [
                              (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(containerStatus.value, (item) => {
                                return (_openBlock(), _createElementBlock("div", {
                                  key: item.vmid,
                                  class: "mobile-card"
                                }, [
                                  _createElementVNode("div", _hoisted_72, [
                                    _createElementVNode("span", _hoisted_73, _toDisplayString(item.displayName || item.description || item.hostname || item.name || '-'), 1),
                                    _createVNode(_component_v_chip, {
                                      size: "x-small",
                                      color: item.type === 'qemu' ? 'primary' : 'info',
                                      class: "ml-2"
                                    }, {
                                      default: _withCtx(() => [
                                        _createTextVNode(_toDisplayString(item.type === 'qemu' ? 'QEMU' : (item.type === 'lxc' ? 'LXC' : item.type)), 1)
                                      ]),
                                      _: 2
                                    }, 1032, ["color"]),
                                    _createVNode(_component_v_chip, {
                                      color: item.status === 'running' ? 'success' : 'grey',
                                      size: "x-small",
                                      class: "ml-2"
                                    }, {
                                      default: _withCtx(() => [
                                        _createTextVNode(_toDisplayString(item.status), 1)
                                      ]),
                                      _: 2
                                    }, 1032, ["color"])
                                  ]),
                                  _createElementVNode("div", _hoisted_74, [
                                    _createElementVNode("span", null, "ID: " + _toDisplayString(item.vmid), 1)
                                  ]),
                                  _createElementVNode("div", _hoisted_75, [
                                    _createVNode(_component_v_icon, {
                                      size: "18",
                                      color: "success",
                                      class: "mr-1"
                                    }, {
                                      default: _withCtx(() => _cache[75] || (_cache[75] = [
                                        _createTextVNode("mdi-timer-outline")
                                      ])),
                                      _: 1
                                    }),
                                    _createElementVNode("span", {
                                      innerHTML: formatUptime(item.uptime)
                                    }, null, 8, _hoisted_76)
                                  ]),
                                  _createElementVNode("div", _hoisted_77, [
                                    _createVNode(_component_v_btn, {
                                      size: "small",
                                      color: "success",
                                      loading: item._actionLoading === 'start',
                                      disabled: item.status === 'running',
                                      onClick: $event => (handleVmAction(item, 'start'))
                                    }, {
                                      default: _withCtx(() => _cache[76] || (_cache[76] = [
                                        _createTextVNode("启动")
                                      ])),
                                      _: 2
                                    }, 1032, ["loading", "disabled", "onClick"]),
                                    _createVNode(_component_v_btn, {
                                      size: "small",
                                      color: "error",
                                      loading: item._actionLoading === 'stop',
                                      disabled: item.status !== 'running',
                                      onClick: $event => (handleVmAction(item, 'stop'))
                                    }, {
                                      default: _withCtx(() => _cache[77] || (_cache[77] = [
                                        _createTextVNode("关闭")
                                      ])),
                                      _: 2
                                    }, 1032, ["loading", "disabled", "onClick"]),
                                    _createVNode(_component_v_btn, {
                                      size: "small",
                                      color: "info",
                                      loading: item._actionLoading === 'reboot',
                                      disabled: item.status !== 'running',
                                      onClick: $event => (handleVmAction(item, 'reboot'))
                                    }, {
                                      default: _withCtx(() => _cache[78] || (_cache[78] = [
                                        _createTextVNode("重启")
                                      ])),
                                      _: 2
                                    }, 1032, ["loading", "disabled", "onClick"]),
                                    _createVNode(_component_v_btn, {
                                      size: "small",
                                      color: "primary",
                                      loading: item._actionLoading === 'snapshot',
                                      onClick: $event => (handleVmSnapshot(item))
                                    }, {
                                      default: _withCtx(() => _cache[79] || (_cache[79] = [
                                        _createTextVNode("快照")
                                      ])),
                                      _: 2
                                    }, 1032, ["loading", "onClick"])
                                  ])
                                ]))
                              }), 128))
                            ]))
                      ])
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
        _createVNode(_component_v_dialog, {
          modelValue: showRestoreDialog.value,
          "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((showRestoreDialog).value = $event)),
          "max-width": "500"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_title, null, {
                  default: _withCtx(() => _cache[80] || (_cache[80] = [
                    _createTextVNode("选择要恢复的备份文件")
                  ])),
                  _: 1
                }),
                _createVNode(_component_v_card_text, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_select, {
                      modelValue: selectedRestoreFile.value,
                      "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((selectedRestoreFile).value = $event)),
                      items: backupFiles.value,
                      "item-title": item => item.filename + ' (' + item.source + ')',
                      "item-value": "filename",
                      label: "备份文件"
                    }, null, 8, ["modelValue", "items", "item-title"]),
                    _createVNode(_component_v_text_field, {
                      modelValue: restoreDisk.value,
                      "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((restoreDisk).value = $event)),
                      label: "恢复存储硬盘",
                      placeholder: "请输入存储池"
                    }, null, 8, ["modelValue"]),
                    _createVNode(_component_v_text_field, {
                      modelValue: restoreVmid.value,
                      "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((restoreVmid).value = $event)),
                      label: "目标VMID(可选)"
                    }, null, 8, ["modelValue"]),
                    _createVNode(_component_v_switch, {
                      modelValue: restoreForce.value,
                      "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((restoreForce).value = $event)),
                      label: "强制恢复(覆盖现有VM)"
                    }, null, 8, ["modelValue"]),
                    _createVNode(_component_v_switch, {
                      modelValue: restoreSkipExisting.value,
                      "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((restoreSkipExisting).value = $event)),
                      label: "跳过已存在的VM"
                    }, null, 8, ["modelValue"])
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_card_actions, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_btn, {
                      color: "grey",
                      onClick: _cache[8] || (_cache[8] = $event => (showRestoreDialog.value = false))
                    }, {
                      default: _withCtx(() => _cache[81] || (_cache[81] = [
                        _createTextVNode("取消")
                      ])),
                      _: 1
                    }),
                    _createVNode(_component_v_btn, {
                      color: "success",
                      loading: loadingRestore.value,
                      onClick: runRestore,
                      disabled: !selectedRestoreFile.value
                    }, {
                      default: _withCtx(() => _cache[82] || (_cache[82] = [
                        _createTextVNode("确认恢复")
                      ])),
                      _: 1
                    }, 8, ["loading", "disabled"])
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
          "onUpdate:modelValue": _cache[10] || (_cache[10] = $event => ((snackbar.value.show) = $event)),
          color: snackbar.value.color,
          timeout: snackbar.value.timeout
        }, {
          default: _withCtx(() => [
            _createTextVNode(_toDisplayString(snackbar.value.text), 1)
          ]),
          _: 1
        }, 8, ["modelValue", "color", "timeout"]),
        _createVNode(_component_v_dialog, {
          modelValue: showDeleteDialog.value,
          "onUpdate:modelValue": _cache[12] || (_cache[12] = $event => ((showDeleteDialog).value = $event)),
          "max-width": "420"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_title, { class: "text-h6" }, {
                  default: _withCtx(() => _cache[83] || (_cache[83] = [
                    _createTextVNode("删除确认")
                  ])),
                  _: 1
                }),
                _createVNode(_component_v_card_text, null, {
                  default: _withCtx(() => [
                    _createElementVNode("div", _hoisted_78, [
                      _cache[84] || (_cache[84] = _createTextVNode(" 确定要删除备份文件 ")),
                      _createElementVNode("span", _hoisted_79, _toDisplayString(deleteTarget.value?.filename), 1),
                      _cache[85] || (_cache[85] = _createTextVNode(" 吗？ "))
                    ]),
                    (deleteTarget.value)
                      ? (_openBlock(), _createElementBlock("div", _hoisted_80, [
                          _createVNode(_component_v_chip, {
                            size: "small",
                            color: "primary",
                            class: "mr-2"
                          }, {
                            default: _withCtx(() => [
                              _createTextVNode(_toDisplayString(deleteTarget.value.source), 1)
                            ]),
                            _: 1
                          }),
                          _createElementVNode("span", _hoisted_81, _toDisplayString(deleteTarget.value.size_mb ? (deleteTarget.value.size_mb.toFixed(2) + ' MB') : '-'), 1)
                        ]))
                      : _createCommentVNode("", true)
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_card_actions, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_spacer),
                    _createVNode(_component_v_btn, {
                      text: "",
                      color: "grey",
                      onClick: _cache[11] || (_cache[11] = $event => (showDeleteDialog.value = false)),
                      disabled: deleteLoading.value
                    }, {
                      default: _withCtx(() => _cache[86] || (_cache[86] = [
                        _createTextVNode("取消")
                      ])),
                      _: 1
                    }, 8, ["disabled"]),
                    _createVNode(_component_v_btn, {
                      color: "error",
                      loading: deleteLoading.value === (deleteTarget.value?.filename + deleteTarget.value?.source),
                      onClick: handleDeleteConfirm
                    }, {
                      default: _withCtx(() => _cache[87] || (_cache[87] = [
                        _createTextVNode(" 删除 ")
                      ])),
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
        _createVNode(_component_v_card_actions, { class: "px-2 py-1 footer-btns" }, {
          default: _withCtx(() => [
            _createVNode(_component_v_btn, {
              class: "glow-btn glow-btn-blue",
              size: "small",
              "prepend-icon": "mdi-history",
              onClick: _cache[13] || (_cache[13] = $event => (showHistoryDialog.value = true))
            }, {
              default: _withCtx(() => _cache[88] || (_cache[88] = [
                _createTextVNode("任务历史")
              ])),
              _: 1
            }),
            _createVNode(_component_v_btn, {
              class: "glow-btn glow-btn-cyan",
              size: "small",
              "prepend-icon": "mdi-file-document-multiple",
              onClick: openBackupFilesDialog
            }, {
              default: _withCtx(() => _cache[89] || (_cache[89] = [
                _createTextVNode("备份文件")
              ])),
              _: 1
            }),
            _createVNode(_component_v_btn, {
              class: "glow-btn glow-btn-purple",
              size: "small",
              "prepend-icon": "mdi-cube-outline",
              onClick: openTemplateImagesDialog,
              disabled: !cleanupTemplateImagesEnabled.value
            }, {
              default: _withCtx(() => _cache[90] || (_cache[90] = [
                _createTextVNode("镜像模板")
              ])),
              _: 1
            }, 8, ["disabled"]),
            _createVNode(_component_v_spacer),
            _createVNode(_component_v_btn, {
              class: "glow-btn glow-btn-red",
              size: "small",
              "prepend-icon": "mdi-delete-sweep",
              disabled: !status.value.enabled || !status.value.auto_cleanup_tmp,
              loading: loadingCleanupTempSpace.value,
              onClick: handleCleanupTempSpace
            }, {
              default: _withCtx(() => _cache[91] || (_cache[91] = [
                _createTextVNode("清理临时空间")
              ])),
              _: 1
            }, 8, ["disabled", "loading"]),
            _createVNode(_component_v_btn, {
              class: "glow-btn glow-btn-gold",
              size: "small",
              "prepend-icon": "mdi-broom",
              disabled: !status.value.enabled || !status.value.enable_log_cleanup,
              loading: loadingCleanupLogs.value,
              onClick: handleCleanupLogs
            }, {
              default: _withCtx(() => _cache[92] || (_cache[92] = [
                _createTextVNode("清理系统日志")
              ])),
              _: 1
            }, 8, ["disabled", "loading"]),
            _createVNode(_component_v_btn, {
              class: "glow-btn glow-btn-orange",
              size: "small",
              "prepend-icon": "mdi-broom",
              loading: loadingClear.value,
              onClick: clearHistory
            }, {
              default: _withCtx(() => _cache[93] || (_cache[93] = [
                _createTextVNode("清理历史记录")
              ])),
              _: 1
            }, 8, ["loading"]),
            _createVNode(_component_v_spacer),
            _createVNode(_component_v_btn, {
              class: "glow-btn glow-btn-purple",
              size: "small",
              "prepend-icon": "mdi-restore",
              loading: loadingRestore.value,
              disabled: !status.value.enabled || !status.value.enable_restore,
              onClick: _cache[14] || (_cache[14] = $event => (openRestoreDialog()))
            }, {
              default: _withCtx(() => _cache[94] || (_cache[94] = [
                _createTextVNode("立即恢复")
              ])),
              _: 1
            }, 8, ["loading", "disabled"]),
            _createVNode(_component_v_btn, {
              class: "glow-btn glow-btn-green",
              size: "small",
              "prepend-icon": "mdi-database-arrow-up",
              loading: loadingBackup.value,
              disabled: !status.value.enabled,
              onClick: runBackup
            }, {
              default: _withCtx(() => _cache[95] || (_cache[95] = [
                _createTextVNode("立即备份")
              ])),
              _: 1
            }, 8, ["loading", "disabled"]),
            _createVNode(_component_v_btn, {
              class: "glow-btn",
              size: "small",
              "prepend-icon": "mdi-stop-circle",
              loading: loadingStopTasks.value,
              onClick: stopAllTasks
            }, {
              default: _withCtx(() => _cache[96] || (_cache[96] = [
                _createTextVNode("停止任务")
              ])),
              _: 1
            }, 8, ["loading"]),
            _createVNode(_component_v_spacer),
            _createVNode(_component_v_btn, {
              class: "glow-btn glow-btn-pink",
              size: "small",
              "prepend-icon": "mdi-cog",
              onClick: _cache[15] || (_cache[15] = $event => (_ctx.$emit('switch')))
            }, {
              default: _withCtx(() => _cache[97] || (_cache[97] = [
                _createTextVNode("配置")
              ])),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_v_dialog, {
          modelValue: showHistoryDialog.value,
          "onUpdate:modelValue": _cache[17] || (_cache[17] = $event => ((showHistoryDialog).value = $event)),
          "max-width": "900"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_title, { class: "text-h6" }, {
                  default: _withCtx(() => _cache[98] || (_cache[98] = [
                    _createTextVNode("任务历史")
                  ])),
                  _: 1
                }),
                _createVNode(_component_v_card_text, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_data_table, {
                      headers: [
              { text: '时间', value: 'timestamp' },
              { text: '类型', value: 'type' },
              { text: '状态', value: 'success' },
              { text: '详情', value: 'message' },
              { text: '消息', value: 'details' }
            ],
                      items: history.value,
                      class: "elevation-0",
                      "hide-default-footer": "",
                      density: "compact",
                      style: {"max-height":"500px","overflow-y":"auto"}
                    }, {
                      "item.timestamp": _withCtx(({ item }) => [
                        _createTextVNode(_toDisplayString(formatTime(item.timestamp)), 1)
                      ]),
                      "item.success": _withCtx(({ item }) => [
                        _createVNode(_component_v_chip, {
                          color: item.success ? 'success' : 'error',
                          size: "small"
                        }, {
                          default: _withCtx(() => [
                            _createTextVNode(_toDisplayString(item.success ? '成功' : '失败'), 1)
                          ]),
                          _: 2
                        }, 1032, ["color"])
                      ]),
                      "item.type": _withCtx(({ item }) => [
                        _createVNode(_component_v_chip, {
                          color: item.type === '备份' ? 'primary' : 'purple',
                          size: "small"
                        }, {
                          default: _withCtx(() => [
                            _createTextVNode(_toDisplayString(item.type), 1)
                          ]),
                          _: 2
                        }, 1032, ["color"])
                      ]),
                      _: 1
                    }, 8, ["items"])
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_card_actions, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_spacer),
                    _createVNode(_component_v_btn, {
                      color: "primary",
                      onClick: _cache[16] || (_cache[16] = $event => (showHistoryDialog.value = false))
                    }, {
                      default: _withCtx(() => _cache[99] || (_cache[99] = [
                        _createTextVNode("关闭")
                      ])),
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
          modelValue: showBackupFilesDialog.value,
          "onUpdate:modelValue": _cache[19] || (_cache[19] = $event => ((showBackupFilesDialog).value = $event)),
          "max-width": "1400"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_title, {
                  class: "text-h6",
                  style: {"padding":"8px 16px 0 16px","font-size":"18px"}
                }, {
                  default: _withCtx(() => _cache[100] || (_cache[100] = [
                    _createTextVNode("备份文件")
                  ])),
                  _: 1
                }),
                _createVNode(_component_v_card_text, { style: {"padding":"0 16px 8px 16px"} }, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_data_table, {
                      headers: backupFileHeaders,
                      items: backupFiles.value,
                      "item-key": "filenameWithSource",
                      class: "elevation-0",
                      "hide-default-footer": "",
                      density: "compact",
                      style: {"margin":"0","padding":"0"}
                    }, {
                      "item.filename": _withCtx(({ item }) => [
                        _createTextVNode(_toDisplayString(item.filename), 1)
                      ]),
                      "item.size_mb": _withCtx(({ item }) => [
                        _createTextVNode(_toDisplayString(item.size_mb ? item.size_mb.toFixed(2) : '-'), 1)
                      ]),
                      "item.date": _withCtx(({ item }) => [
                        _createTextVNode(_toDisplayString(item.time_str ? item.time_str.split(' ')[0] : '-'), 1)
                      ]),
                      "item.time": _withCtx(({ item }) => [
                        _createTextVNode(_toDisplayString(item.time_str ? (item.time_str.split(' ')[1] || '-') : '-'), 1)
                      ]),
                      "item.actions": _withCtx(({ item }) => [
                        _createElementVNode("div", _hoisted_82, [
                          (!status.value.enabled)
                            ? (_openBlock(), _createBlock(_component_v_tooltip, {
                                key: 0,
                                text: "请先启用插件"
                              }, {
                                activator: _withCtx(({ props }) => [
                                  _createVNode(_component_v_btn, _mergeProps({
                                    icon: "",
                                    size: "x-small",
                                    disabled: !status.value.enabled
                                  }, props), {
                                    default: _withCtx(() => [
                                      _createVNode(_component_v_icon, { icon: "mdi-download" })
                                    ]),
                                    _: 2
                                  }, 1040, ["disabled"])
                                ]),
                                _: 1
                              }))
                            : (_openBlock(), _createBlock(_component_v_btn, {
                                key: 1,
                                icon: "",
                                size: "x-small",
                                onClick: $event => (downloadBackup(item))
                              }, {
                                default: _withCtx(() => [
                                  _createVNode(_component_v_icon, { icon: "mdi-download" })
                                ]),
                                _: 2
                              }, 1032, ["onClick"])),
                          (!status.value.enabled || !status.value.enable_restore)
                            ? (_openBlock(), _createBlock(_component_v_tooltip, {
                                key: 2,
                                text: "请先启用插件并开启恢复功能"
                              }, {
                                activator: _withCtx(({ props }) => [
                                  _createVNode(_component_v_btn, _mergeProps({
                                    icon: "",
                                    size: "x-small",
                                    color: "success",
                                    disabled: !status.value.enabled || !status.value.enable_restore
                                  }, props), {
                                    default: _withCtx(() => [
                                      _createVNode(_component_v_icon, { icon: "mdi-restore" })
                                    ]),
                                    _: 2
                                  }, 1040, ["disabled"])
                                ]),
                                _: 1
                              }))
                            : (_openBlock(), _createBlock(_component_v_btn, {
                                key: 3,
                                icon: "",
                                size: "x-small",
                                color: "success",
                                onClick: $event => (openRestoreDialog(item))
                              }, {
                                default: _withCtx(() => [
                                  _createVNode(_component_v_icon, { icon: "mdi-restore" })
                                ]),
                                _: 2
                              }, 1032, ["onClick"])),
                          (!status.value.enabled)
                            ? (_openBlock(), _createBlock(_component_v_tooltip, {
                                key: 4,
                                text: "请先启用插件"
                              }, {
                                activator: _withCtx(({ props }) => [
                                  _createVNode(_component_v_btn, _mergeProps({
                                    icon: "",
                                    size: "x-small",
                                    color: "error",
                                    disabled: !status.value.enabled
                                  }, props), {
                                    default: _withCtx(() => [
                                      _createVNode(_component_v_icon, { icon: "mdi-delete" })
                                    ]),
                                    _: 2
                                  }, 1040, ["disabled"])
                                ]),
                                _: 1
                              }))
                            : (_openBlock(), _createBlock(_component_v_btn, {
                                key: 5,
                                icon: "",
                                size: "x-small",
                                color: "error",
                                onClick: $event => (confirmDelete(item))
                              }, {
                                default: _withCtx(() => [
                                  _createVNode(_component_v_icon, { icon: "mdi-delete" })
                                ]),
                                _: 2
                              }, 1032, ["onClick"]))
                        ])
                      ]),
                      _: 1
                    }, 8, ["items"])
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_card_actions, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_spacer),
                    _createVNode(_component_v_btn, {
                      color: "primary",
                      onClick: _cache[18] || (_cache[18] = $event => (showBackupFilesDialog.value = false))
                    }, {
                      default: _withCtx(() => _cache[101] || (_cache[101] = [
                        _createTextVNode("关闭")
                      ])),
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
          modelValue: showCheckupDialog.value,
          "onUpdate:modelValue": _cache[22] || (_cache[22] = $event => ((showCheckupDialog).value = $event)),
          "max-width": "480"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_card, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_card_title, { class: "d-flex align-center" }, {
                  default: _withCtx(() => [
                    _createElementVNode("span", _hoisted_83, _toDisplayString(checkupReport.value.avatar), 1),
                    _cache[103] || (_cache[103] = _createElementVNode("span", { style: {"font-size":"1.15rem","font-weight":"600"} }, "体检报告", -1)),
                    _createVNode(_component_v_spacer),
                    _createVNode(_component_v_btn, {
                      icon: "",
                      onClick: _cache[20] || (_cache[20] = $event => (showCheckupDialog.value=false))
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_v_icon, null, {
                          default: _withCtx(() => _cache[102] || (_cache[102] = [
                            _createTextVNode("mdi-close")
                          ])),
                          _: 1
                        })
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_card_text, null, {
                  default: _withCtx(() => [
                    _createElementVNode("div", _hoisted_84, "总分：" + _toDisplayString(checkupReport.value.total || 0) + "/100", 1),
                    _createElementVNode("div", _hoisted_85, _toDisplayString(checkupReport.value.comment), 1),
                    _createVNode(_component_v_list, { dense: "" }, {
                      default: _withCtx(() => [
                        (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(checkupReport.value.items, (item) => {
                          return (_openBlock(), _createBlock(_component_v_list_item, {
                            key: item.label
                          }, {
                            default: _withCtx(() => [
                              _createVNode(_component_v_list_item_content, null, {
                                default: _withCtx(() => [
                                  _createVNode(_component_v_list_item_title, null, {
                                    default: _withCtx(() => [
                                      _createTextVNode(_toDisplayString(item.label) + "：", 1),
                                      _createElementVNode("b", null, _toDisplayString(item.result), 1),
                                      _cache[104] || (_cache[104] = _createTextVNode()),
                                      _createElementVNode("span", _hoisted_86, "+" + _toDisplayString(item.score), 1)
                                    ]),
                                    _: 2
                                  }, 1024),
                                  _createVNode(_component_v_list_item_subtitle, { style: {"font-size":"0.95rem","color":"#90caf9"} }, {
                                    default: _withCtx(() => [
                                      _createTextVNode(_toDisplayString(item.detail), 1)
                                    ]),
                                    _: 2
                                  }, 1024)
                                ]),
                                _: 2
                              }, 1024)
                            ]),
                            _: 2
                          }, 1024))
                        }), 128))
                      ]),
                      _: 1
                    }),
                    _createElementVNode("div", _hoisted_87, _toDisplayString(checkupReport.value.blessing), 1)
                  ]),
                  _: 1
                }),
                _createVNode(_component_v_card_actions, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_v_spacer),
                    _createVNode(_component_v_btn, {
                      color: "primary",
                      onClick: _cache[21] || (_cache[21] = $event => (showCheckupDialog.value=false))
                    }, {
                      default: _withCtx(() => _cache[105] || (_cache[105] = [
                        _createTextVNode("关闭")
                      ])),
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
        }, 8, ["modelValue"])
      ]),
      _: 1
    }),
    _createVNode(_component_v_dialog, {
      modelValue: showHostActionDialog.value,
      "onUpdate:modelValue": _cache[24] || (_cache[24] = $event => ((showHostActionDialog).value = $event)),
      "max-width": "400"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, {
              class: "d-flex align-center",
              style: _normalizeStyle(`color:${pendingHostAction.value==='shutdown'?'#d32f2f':'#1976d2'};font-weight:600;`)
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  color: pendingHostAction.value==='shutdown'?'error':'info',
                  size: "32",
                  class: "mr-2"
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(_toDisplayString(pendingHostAction.value==='shutdown' ? 'mdi-power' : 'mdi-restart'), 1)
                  ]),
                  _: 1
                }, 8, ["color"]),
                _createTextVNode(" " + _toDisplayString(pendingHostAction.value==='shutdown' ? '关机主机' : '重启主机'), 1)
              ]),
              _: 1
            }, 8, ["style"]),
            _createVNode(_component_v_card_text, null, {
              default: _withCtx(() => [
                _createElementVNode("div", _hoisted_88, [
                  _cache[106] || (_cache[106] = _createTextVNode(" 确定要")),
                  _createElementVNode("strong", null, _toDisplayString(pendingHostAction.value==='shutdown' ? '关机' : '重启'), 1),
                  _cache[107] || (_cache[107] = _createTextVNode("当前PVE主机吗？")),
                  _cache[108] || (_cache[108] = _createElementVNode("br", null, null, -1)),
                  (pendingHostAction.value==='shutdown')
                    ? (_openBlock(), _createElementBlock("span", _hoisted_89, "关机后需物理开机或远程唤醒！"))
                    : (_openBlock(), _createElementBlock("span", _hoisted_90, "重启期间主机将短暂不可用。"))
                ])
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  text: "",
                  color: "grey",
                  onClick: _cache[23] || (_cache[23] = $event => (showHostActionDialog.value=false)),
                  disabled: hostActionLoading.value === pendingHostAction.value
                }, {
                  default: _withCtx(() => _cache[109] || (_cache[109] = [
                    _createTextVNode("取消")
                  ])),
                  _: 1
                }, 8, ["disabled"]),
                _createVNode(_component_v_btn, {
                  color: pendingHostAction.value==='shutdown'?'error':'info',
                  loading: hostActionLoading.value === pendingHostAction.value,
                  onClick: doHostAction
                }, {
                  default: _withCtx(() => [
                    _createTextVNode(" 确认" + _toDisplayString(pendingHostAction.value==='shutdown' ? '关机' : '重启'), 1)
                  ]),
                  _: 1
                }, 8, ["color", "loading"])
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
      modelValue: showTemplateImagesDialog.value,
      "onUpdate:modelValue": _cache[26] || (_cache[26] = $event => ((showTemplateImagesDialog).value = $event)),
      "max-width": "1400"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_v_card, null, {
          default: _withCtx(() => [
            _createVNode(_component_v_card_title, {
              class: "text-h6",
              style: {"padding":"8px 16px 0 16px","font-size":"18px"}
            }, {
              default: _withCtx(() => _cache[110] || (_cache[110] = [
                _createTextVNode("镜像模板管理")
              ])),
              _: 1
            }),
            _createVNode(_component_v_card_text, { style: {"padding":"0 16px 8px 16px"} }, {
              default: _withCtx(() => [
                _createVNode(_component_v_data_table, {
                  headers: templateImageHeaders.filter(h => h.value !== 'actions'),
                  items: templateImages.value,
                  "item-key": "filenameWithType",
                  class: "elevation-0",
                  "hide-default-footer": "",
                  density: "compact",
                  style: {"margin":"0","padding":"0"}
                }, {
                  "item.filename": _withCtx(({ item }) => [
                    _createTextVNode(_toDisplayString(item.filename), 1)
                  ]),
                  "item.type": _withCtx(({ item }) => [
                    _createVNode(_component_v_chip, {
                      size: "x-small",
                      color: item.type === 'iso' ? 'info' : 'purple'
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode(_toDisplayString(item.type === 'iso' ? 'ISO镜像' : 'CT模板'), 1)
                      ]),
                      _: 2
                    }, 1032, ["color"])
                  ]),
                  "item.size_mb": _withCtx(({ item }) => [
                    _createTextVNode(_toDisplayString(item.size_mb ? item.size_mb.toFixed(2) : '-'), 1)
                  ]),
                  "item.date": _withCtx(({ item }) => [
                    _createTextVNode(_toDisplayString(item.date || '-'), 1)
                  ]),
                  _: 1
                }, 8, ["headers", "items"])
              ]),
              _: 1
            }),
            _createVNode(_component_v_card_actions, null, {
              default: _withCtx(() => [
                _createVNode(_component_v_spacer),
                _createVNode(_component_v_btn, {
                  color: "primary",
                  class: "ml-2",
                  onClick: _cache[25] || (_cache[25] = $event => (showTemplateImagesDialog.value = false))
                }, {
                  default: _withCtx(() => _cache[111] || (_cache[111] = [
                    _createTextVNode("关闭")
                  ])),
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
    }, 8, ["modelValue"])
  ], 64))
}
}

};
const PageComponent = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-77586690"]]);

export { PageComponent as default };
