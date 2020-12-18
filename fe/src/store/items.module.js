import {
  ItemsService
} from "@/common/api.service";

import {
  LanguageHelper
} from "@/common/language.helper";

import {
  FETCH_ITEMS,
  FETCH_ITEMS_PROCESSING,
  UPLOAD_FILES,
  DOWNLOAD_SPLITTED,
  DOWNLOAD_PROCESSING,
  GET_SPLITTED,
  GET_DOC_INDEX,
  GET_PROCESSING,
  GET_CANDIDATES,
  EDIT_PROCESSING,
  STOP_ALIGNMENT,
  ALIGN_SPLITTED
} from "./actions.type";

import {
  SET_ITEMS,
  SET_ITEMS_PROCESSING,
  SET_SPLITTED,
  SET_PROCESSING,
  SET_DOC_INDEX
} from "./mutations.type";

const initialState = {
  items: LanguageHelper.initItems(),
  itemsProcessing: LanguageHelper.initItems(),
  splitted: LanguageHelper.initSplitted(),
  processing: LanguageHelper.initProcessing(),
  docIndex: []
};

export const state = {
  ...initialState
};

export const actions = {
  async [FETCH_ITEMS](context, params) {
    const {
      data
    } = await ItemsService.fetchItems(params);
    context.commit(SET_ITEMS, {
      items: data.items,
      langCode: params.langCode
    });
    return data;
  },
  async [FETCH_ITEMS_PROCESSING](context, params) {
    const {
      data
    } = await ItemsService.fetchItemsProcessing(params);
    context.commit(SET_ITEMS_PROCESSING, {
      items: data.items[params.langCodeFrom],
      langCode: params.langCodeFrom
    });
    return data;
  },
  // params {file, username, langCode}
  async [UPLOAD_FILES](context, params) {
    await ItemsService.upload(params);
  },
  // params {fileId, username, langCode, fileName}
  async [DOWNLOAD_SPLITTED](context, params) {
    await ItemsService.downloadSplitted(params);
  },
  // params {fileId, username, langCode, fileName}
  async [DOWNLOAD_PROCESSING](context, params) {
    await ItemsService.downloadProcessing(params);
  },
  // params {fileId, username, langCode, count, page}
  async [GET_SPLITTED](context, params) {
    const {
      data
    } = await ItemsService.getSplitted(params);
    context.commit(SET_SPLITTED, {
      data: data,
      langCode: params.langCode
    });
    return;
  },
  async [GET_DOC_INDEX](context, params) {
    await ItemsService.getDocIndex(params).then(
      function (response) {
        // console.log("setting index", response.data)
        context.commit(SET_DOC_INDEX, response.data);
      },
      function () {
        console.log(`Didn't find database.`);
      }
    );
  },
  async [GET_PROCESSING](context, params) {
    await ItemsService.getProcessing(params).then(
      function (response) {
        context.commit(SET_PROCESSING, response.data);
      },
      function () {
        console.log(`Didn't find processing document.`);
      }
    );
    return;
  },
  async [GET_CANDIDATES](context, params) {
    return await ItemsService.getCandidates(params);
  },
  async [STOP_ALIGNMENT](context, params) {
    await ItemsService.stopAlignment(params);
    return;
  },
  // params {fileId, username}
  async [EDIT_PROCESSING](context, params) {
    await ItemsService.editProcessing(params).then(
      () => {
        console.log(`EDIT_PROCESSING OK. Getting index.`);
        context.dispatch(GET_DOC_INDEX, {
          username: params.username,
          langCodeFrom: params.langCodeFrom,
          langCodeTo: params.langCodeTo,
          fileId: params.fileId
        })
      },
      function () {
        console.log(`Didn't find processing document.`);
      }
    );
    return;
  },
  async [ALIGN_SPLITTED](context, params) {
    await ItemsService.alignSplitted(params);
  }
};

export const mutations = {
  [SET_ITEMS](state, params) {
    state.items[params.langCode] = params.items[params.langCode];
  },
  [SET_ITEMS_PROCESSING](state, params) {
    state.itemsProcessing[params.langCode] = params.items;
  },
  [SET_SPLITTED](state, params) {
    if (params.data.items[params.langCode]) {
      state.splitted[params.langCode].lines = params.data.items[params.langCode];
    }
    if (params.data.meta[params.langCode]) {
      state.splitted[params.langCode].meta = params.data.meta[params.langCode];
    }
  },
  [SET_PROCESSING](state, data) {
    state.processing = data;
  },
  [SET_DOC_INDEX](state, data) {
    // console.log("new index:", data.items)
    state.docIndex = data.items;
  }
};

const getters = {
  items(state) {
    return state.items;
  },
  itemsProcessing(state) {
    return state.itemsProcessing;
  },
  splitted(state) {
    return state.splitted;
  },
  processing(state) {
    return state.processing;
  },
  docIndex(state) {
    return state.docIndex;
  },
};

export default {
  state,
  actions,
  mutations,
  getters
};