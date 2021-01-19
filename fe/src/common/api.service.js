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
      throw new Error(`ApiService ${error}`);
    });
  },
  get(resource, slug = "") {
    return Vue.axios.get(`${resource}/${slug}`).catch(error => {
      throw new Error(`ApiService ${error}`);
    });
  },
  download(resource, slug = "") {
    return Vue.axios.get(`${resource}/${slug}`, {
      responseType: 'blob'
    }).catch(error => {
      throw new Error(`ApiService ${error}`);
    });
  },
  post(resource, slug, params) {
    return Vue.axios.post(`${resource}/${slug}`, params).catch(error => {
      throw new Error(`ApiService ${error}`);
    });
  },
  update(resource, slug, params) {
    return Vue.axios.put(`${resource}/${slug}`, params);
  },
  put(resource, params) {
    return Vue.axios.put(`${resource}`, params);
  },
  delete(resource) {
    return Vue.axios.delete(resource).catch(error => {
      throw new Error(`ApiService ${error}`);
    });
  }
};

export default ApiService;

export const ItemsService = {
  initUserspace(params) {
    return ApiService.get("items", `${params.username}/init`);
  },
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
  getCandidates(params) {
    return ApiService.get(
      "items",
      `${params.username}/processing/${params.langCodeFrom}/${params.langCodeTo}/${params.fileId}/candidates/${params.textType}/${params.indexId}/${params.countBefore}/${params.countAfter}`
    );
  },
  getDocIndex(params) {
    return ApiService.get(
      "items",
      `${params.username}/processing/${params.langCodeFrom}/${params.langCodeTo}/${params.fileId}/index`
    );
  },
  getSplittedByIds(params) {
    console.log("getSplittedByIds", params)
    let form = new FormData();
    form.append("ids", params.ids);
    return ApiService.post(
      "items",
      `${params.username}/splitted/${params.type}/${params.langCodeFrom}/${params.langCodeTo}/${params.align_guid}`,
      form
    );
  },
  stopAlignment(params) {
    return ApiService.post(
      "items",
      `${params.username}/align/stop/${params.langCodeFrom}/${params.langCodeTo}/${params.alignId}`
    );
  },
  startAlignment(params) {
    let form = new FormData();
    form.append("id", params.id);
    form.append("align_all", params.alignAll);
    form.append("batch_ids", JSON.stringify(params.batchIds))
    return ApiService.post(
      "items",
      `${params.username}/alignment/align`,
      form
    );
  },
  createAlignment(params) {
    let form = new FormData();
    form.append("id_from", params.idFrom);
    form.append("id_to", params.idTo);
    form.append("name", params.name);
    return ApiService.post(
      "items",
      `${params.username}/alignment/create`,
      form
    );
  },
  editProcessing(params) {
    let form = new FormData();
    form.append("text", params.text);
    form.append("text_type", params.text_type);
    form.append("operation", params.operation);
    form.append("index_id", params.indexId);
    form.append("target", params.target);
    form.append("candidate_line_id", params.candidateLineId);
    form.append("candidate_text", params.candidateText);
    form.append("batch_id", params.batchId);
    form.append("batch_index_id", params.batchIndexId);

    return ApiService.post(
      "items",
      `${params.username}/processing/${params.langCodeFrom}/${params.langCodeTo}/${params.fileId}/edit`,
      form
    );
  },
};
