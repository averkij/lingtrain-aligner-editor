<style>
  @import './assets/styles/main.css';
</style>

<template>
  <v-app>
    <!-- <Header /> -->
    <v-main>
      <v-container class="pb-15">
        <router-view></router-view>
      </v-container>
    </v-main>
    <Footer />
  </v-app>
</template>

<script>
// import Header from "@/components/Header"
import Footer from "@/components/Footer";

export default {
  name: "App",
  components: {
    // Header,
    Footer
  }
};
</script>
