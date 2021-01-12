<style>
@import "./assets/styles/main.css";
</style>

<template>
  <v-app>
    <!-- Left drawer menu -->
    <v-navigation-drawer app v-model="drawer" temporary>
      <v-list nav dense>
        <v-list-item-group
          v-model="group"
          active-class="blue--text text--accent-4"
        >
          <v-list-item>
            <v-list-item-icon>
              <v-icon>mdi-home</v-icon>
            </v-list-item-icon>
            <v-list-item-title>Home</v-list-item-title>
          </v-list-item>

          <v-list-item>
            <v-list-item-icon>
              <v-icon>mdi-account</v-icon>
            </v-list-item-icon>
            <v-list-item-title>Account</v-list-item-title>
          </v-list-item>
        </v-list-item-group>
      </v-list>
    </v-navigation-drawer>

    <!-- Top app bar -->
    <v-app-bar app color="primary" dark hide-on-scroll>
      <v-row>
        <v-col cols="12" sm="1">
          <v-app-bar-nav-icon @click="drawer = true"></v-app-bar-nav-icon>
        </v-col>

        <v-col cols="12" sm="5" class="text-right">
          <v-app-bar-title class="pa-2 font-josefin">Russian</v-app-bar-title>
          <v-app-bar-nav-icon>
            <v-img
              class="ma-2"
              src="@/assets/flags/flag-ru-h.svg"
              width="35px"
              height="35px" /></v-app-bar-nav-icon
        ></v-col>

        <v-col cols="12" sm="6"
          ><v-app-bar-nav-icon>
            <v-img
              class="ma-2"
              src="@/assets/flags/flag-cn-h.svg"
              width="35px"
              height="35px"
          /></v-app-bar-nav-icon>
          <v-app-bar-title class="pa-2 font-josefin">Chinese</v-app-bar-title>
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

export default {
  name: "App",
  components: {
    Footer,
  },
  data: () => ({
    drawer: false,
    group: null,
  }),
};
</script>
