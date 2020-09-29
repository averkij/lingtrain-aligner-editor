import Vue from "vue";
import VueRouter from "vue-router";
import { DEFAULT_FROM, DEFAULT_TO } from "@/common/language.helper";

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
    path: "/user/:username/items/:from/:to",
    name: "items",
    component: () => import("@/views/Items")
  },
  {
    path: "/user/:username",
    redirect: `/user/:username/items/${DEFAULT_FROM}/${DEFAULT_TO}`
  },
  {
    path: "/user/:username/items",
    redirect: `/user/:username/items/${DEFAULT_FROM}/${DEFAULT_TO}`
  }
];

const router = new VueRouter({
  mode: 'history',
  routes
});

export default router;
