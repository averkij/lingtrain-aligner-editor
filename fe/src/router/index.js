import Vue from "vue";
import VueRouter from "vue-router";

Vue.use(VueRouter);

const routes = [
  {
    path: "/",
    name: "home",
    component: () => import("@/views/Login")
  },
  {
    path: "/login",
    name: "login",
    component: () => import("@/views/Login"),
    alias: "/user"
  },
  {
    path: "/user/:username",
    name: "items",
    component: () => import("@/views/Items")
  }
];

const router = new VueRouter({
  mode: 'history',
  routes
});

export default router;
