/**
 * Browser injection hooks for intercepting media requests
 */

export const HOOKS_SCRIPT = `(() => {
  const logs = [];
  const push = (type, payload) => {
    try {
      logs.push({
        t: Date.now(),
        type,
        payload
      });
    } catch (e) {}
  };

  const origFetch = window.fetch;
  window.fetch = async function(...args) {
    const input = args[0];
    const url = typeof input === "string" ? input : input?.url;
    push("fetch:request", { url });
    const resp = await origFetch.apply(this, args);
    try {
      push("fetch:response", {
        url: resp.url,
        contentType: resp.headers.get("content-type")
      });
    } catch (e) {}
    return resp;
  };

  const origOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function(method, url, ...rest) {
    this.__hook_method = method;
    this.__hook_url = url;
    push("xhr:open", { method, url });
    return origOpen.call(this, method, url, ...rest);
  };

  const origSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.send = function(...args) {
    this.addEventListener("load", function() {
      try {
        push("xhr:load", {
          method: this.__hook_method,
          url: this.__hook_url,
          status: this.status,
          contentType: this.getResponseHeader("content-type")
        });
      } catch (e) {}
    });
    return origSend.apply(this, args);
  };

  const origCreateObjectURL = URL.createObjectURL;
  URL.createObjectURL = function(obj) {
    const blobUrl = origCreateObjectURL.call(this, obj);
    push("blob:createObjectURL", {
      blobUrl,
      constructorName: obj?.constructor?.name,
      size: obj?.size
    });
    return blobUrl;
  };
})();`;
