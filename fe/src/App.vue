<style>
  @import "./assets/styles/main.css";
</style>

<template>
  <v-app>
    <!-- Left drawer menu -->
    <v-navigation-drawer app v-model="drawer" temporary>
      <v-list nav dense>
        <v-list-item-group v-model="group" active-class="blue--text text--accent-4">
          <v-list-item>
            <v-list-item-icon>
              <v-icon>mdi-view-list-outline</v-icon>
            </v-list-item-icon>
            <v-list-item-title @click.stop.prevent="openContents()">Contents</v-list-item-title>
          </v-list-item>
          <v-list-item>
            <v-list-item-icon>
              <v-icon>mdi-github</v-icon>
            </v-list-item-icon>
            <v-list-item-title @click.stop.prevent="goToGithub()">Github</v-list-item-title>
          </v-list-item>

          <!-- <v-list-item>
            <v-list-item-icon>
              <v-icon>mdi-account</v-icon>
            </v-list-item-icon>
            <v-list-item-title>Account</v-list-item-title>
          </v-list-item> -->
        </v-list-item-group>
      </v-list>
    </v-navigation-drawer>

    <!-- Top app bar -->
    <v-app-bar app color="primary" dark hide-on-scroll>
      <v-row>
        <v-col v-if="showDrawerMenu" cols="12" sm="1">
          <v-app-bar-nav-icon @click="drawer = true"></v-app-bar-nav-icon>
        </v-col>

        <v-col v-if="showLanguageBar" cols="12" sm="5" class="text-right">
          <div class="pa-2 font-josefin d-inline-block">{{
            LANGUAGES[langCodeFrom].name
          }}</div>
          <v-menu offset-y>
            <template v-slot:activator="{ on, attrs }">
              <v-btn icon color="yellow" v-bind="attrs" v-on="on">
                <v-img class="ma-2" :src="getFlagImgPath(langCodeFrom)" width="35px" height="35px" />
              </v-btn>
            </template>
            <v-list>
              <v-list-item v-for="(item, i) in LANGUAGES" :key="i" link>
                <v-list-item-title @click="changeLangFrom(item.langCode)">
                  <div class="d-flex">
                    <v-img class="" :src="getFlagImgPath(item.langCode)" max-width="35" max-height="35" />
                    <div class="ml-4 align-self-center">{{ item.name }}</div>
                  </div>
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </v-col>

        <v-col v-if="showLanguageBar" cols="12" sm="6">
          <v-menu offset-y>
            <template v-slot:activator="{ on, attrs }">
              <v-btn icon color="yellow" v-bind="attrs" v-on="on">
                <v-img class="ma-2" :src="getFlagImgPath(langCodeTo)" width="35px" height="35px" />
              </v-btn>
            </template>
            <v-list>
              <v-list-item v-for="(item, i) in LANGUAGES" :key="i" link>
                <v-list-item-title @click="changeLangTo(item.langCode)">
                  <div class="d-flex">
                    <v-img class="" :src="getFlagImgPath(item.langCode)" max-width="35" max-height="35" />
                    <div class="ml-4 align-self-center">{{ item.name }}</div>
                  </div>
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
          <div class="pa-2 font-josefin d-inline-block">{{
            LANGUAGES[langCodeTo].name
          }}</div>
        </v-col>
      </v-row>
    </v-app-bar>

    <v-main>
      <v-container class="pb-15">
        <router-view></router-view>
      </v-container>
    </v-main>

    <Footer />
  </v-app>
</template>

<script>
  import Footer from "@/components/Footer";
  import {
    LANGUAGES
  } from "@/common/language.helper";
  import {
    DEFAULT_FROM,
    DEFAULT_TO
  } from "@/common/language.helper";
  import {
    API_URL
  } from "@/common/config";

  export default {
    name: "App",
    components: {
      Footer,
    },
    data: () => ({
      API_URL,
      LANGUAGES,
      drawer: false,
      group: null,
    }),
    methods: {
      // getFlagImgPath(code) {
      //   return require(`@/assets/flags/flag-${code}-h.svg`);
      // },
      getFlagImgPath(code) {
        return `${API_URL}/static/flags/flag-${code}-h.svg`;
      },
      changeLangFrom(code) {
        this.$router.push({
          path: `/user/${this.$route.params.username}/items/${code}/${this.langCodeTo}`,
        });
      },
      changeLangTo(code) {
        this.$router.push({
          path: `/user/${this.$route.params.username}/items/${this.langCodeFrom}/${code}`,
        });
      },
      goToGithub() {
        window.open("https://github.com/averkij/lingtrain-aligner", '_blank');
      },
      openContents() {
        this.$router.push({
          path: `/contents`,
        });
      }
    },
    computed: {
      langCodeFrom() {
        let langCode = this.$route.params.from;
        if (this.LANGUAGES[langCode]) {
          return langCode;
        }
        return DEFAULT_FROM;
      },
      langCodeTo() {
        let langCode = this.$route.params.to;
        if (this.LANGUAGES[langCode]) {
          return langCode;
        }
        return DEFAULT_TO;
      },
      showLanguageBar() {
        return this.$route.name == "items";
      },
      showDrawerMenu() {
        return this.$route.name != "login" && this.$route.name != "home";
      },
    },
  };
</script>
