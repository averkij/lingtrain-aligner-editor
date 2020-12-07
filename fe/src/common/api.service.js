import Vue from "vue";
import axios from "axios";
import VueAxios from "vue-axios";
import {
  API_URL
} from "@/common/config";

const ApiService = {
  init() {
    Vue.use(VueAxios, axios);
    Vue.axios.defaults.baseURL = API_URL;
  },
  query(resource, params) {
    return Vue.axios.get(resource, params).catch(error => {
      throw new Error(`[TAP] ApiService ${error}`);
    });
  },
  get(resource, slug = "") {
    return Vue.axios.get(`${resource}/${slug}`).catch(error => {
      throw new Error(`[TAP] ApiService ${error}`);
    });
  },
  download(resource, slug = "") {
    return Vue.axios.get(`${resource}/${slug}`, {
      responseType: 'blob'
    }).catch(error => {
      throw new Error(`[TAP] ApiService ${error}`);
    });
  },
  post(resource, slug, params) {
    return Vue.axios.post(`${resource}/${slug}`, params);
  },
  update(resource, slug, params) {
    return Vue.axios.put(`${resource}/${slug}`, params);
  },
  put(resource, params) {
    return Vue.axios.put(`${resource}`, params);
  },
  delete(resource) {
    return Vue.axios.delete(resource).catch(error => {
      throw new Error(`[TAP] ApiService ${error}`);
    });
  }
};

export default ApiService;

export const ItemsService = {
  fetchItems(params) {
    return ApiService.get("items",
    `${params.username}/raw/${params.langCode}`);
  },
  fetchItemsProcessing(params) {
    return ApiService.get(
      "items",
      `${params.username}/processing/list/${params.langCodeFrom}/${params.langCodeTo}`
    );
  },
  upload(params) {
    //check filesize
    if (!params.file) {
      alert("File is empty");
      return;
    }
    if (params.file.size > 5 * 1024 * 1024) {
      alert("File is too big (> 5MB)");
      return;
    }
    let form = new FormData();
    form.append(params.langCode, params.file);
    form.append("type", params.isProxy ? "proxy" : "raw");
    form.append("rawFileName", params.rawFileName);
    return ApiService.post("items",
      `${params.username}/raw/${params.langCode}`,
      form);
  },
  downloadSplitted(params) {
    return ApiService.get(
      "items",
      `${params.username}/splitted/${params.langCode}/${params.fileId}/download`
    ).then((response) => {
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', params.fileName);
      document.body.appendChild(link);
      link.click();
    });
  },
  downloadProcessing(params) {
    return ApiService.get(
      "items",
      `${params.username}/processing/${params.langCodeFrom}/${params.langCodeTo}/${params.fileId}/download/${params.langCodeDownload}/${params.format}/${params.threshold}`
    ).then((response) => {
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', params.fileName);
      document.body.appendChild(link);
      link.click();
    });
  },
  getSplitted(params) {
    return ApiService.get(
      "items",
      `${params.username}/splitted/${params.langCode}/${params.fileId}/${params.linesCount}/${params.page}`
    );
  },
  getProcessing(params) {
    return ApiService.get(
      "items",
      `${params.username}/processing/${params.langCodeFrom}/${params.langCodeTo}/${params.fileId}/${params.linesCount}/${params.page}`
    );
  },
  stopAlignment(params) {
    return ApiService.post(
      "items",
      `${params.username}/align/stop/${params.langCodeFrom}/${params.langCodeTo}/${params.fileId}`
    );
  },
  alignSplitted(params) {
    return ApiService.get(
      "items",
      `${params.username}/align/${params.langCodeFrom}/${params.langCodeTo}/${params.fileIds[params.langCodeFrom]}/${params.fileIds[params.langCodeTo]}`
    );
  },
  editProcessing(params) {
    let form = new FormData();
    form.append("line_id", params.line_id);
    form.append("text", params.text);
    form.append("text_type", params.text_type);
    return ApiService.post(
      "items",
      `${params.username}/processing/${params.langCodeFrom}/${params.langCodeTo}/${params.fileId}/edit`,
      form
    );
  },
};