import "@mdi/font/css/materialdesignicons.css";
import Vue from "vue";
import Vuetify from "vuetify/lib";
import vueNumeralFilterInstaller from "vue-numeral-filter";

Vue.use(Vuetify);
Vue.use(vueNumeralFilterInstaller, { locale: "en-gb" });

export default new Vuetify({
  icons: {
    iconfont: "mdi"
  }
});

// npm install @mdi/font -D
// npm install @mdi/js -D
