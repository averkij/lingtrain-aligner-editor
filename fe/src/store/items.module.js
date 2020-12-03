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
  GET_PROCESSING,
  EDIT_PROCESSING,
  STOP_ALIGNMENT,
  ALIGN_SPLITTED
} from "./actions.type";

import {
  SET_ITEMS,
  SET_ITEMS_PROCESSING,
  SET_SPLITTED,
  SET_PROCESSING,
} from "./mutations.type";

const initialState = {
  items: LanguageHelper.initItems(),
  itemsProcessing: LanguageHelper.initItems(),
  splitted: LanguageHelper.initSplitted(),
  processing: LanguageHelper.initProcessing()
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

    console.log("FETCH_ITEMS_PROCESSING params", params)

    console.log(">>>data:", data.items)

    context.commit(SET_ITEMS_PROCESSING, {
      items: data.items,
      langCode: params.langCodeFrom
    });
    return data;
  },
  // params {file, username, langCode}
  async [UPLOAD_FILES](context, params) {
    await ItemsService.upload(params);
    await context.dispatch(FETCH_ITEMS, params);
    return;
  },
  // params {fileId, username, langCode, fileName}
  async [DOWNLOAD_SPLITTED](context, params) {
    await ItemsService.downloadSplitted(params);
    return;
  },
  // params {fileId, username, langCode, fileName}
  async [DOWNLOAD_PROCESSING](context, params) {
    await ItemsService.downloadProcessing(params);
    return;
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
  // params {fileId, username}
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
  async [STOP_ALIGNMENT](context, params) {
    await ItemsService.stopAlignment(params);
    return;
  },
  // params {fileId, username}
  [EDIT_PROCESSING](context, params) {
    return ItemsService.editProcessing(params);
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
    console.log("params.items", params.items)
    console.log("params.langCode", params.langCode)
    console.log("state.itemsProcessing", state.itemsProcessing)

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
  }
};

export default {
  state,
  actions,
  mutations,
  getters
};