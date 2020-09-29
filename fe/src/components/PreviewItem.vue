<template>
  <div>
    <v-row justify="center" no-gutters>
      <v-col class="text-left" cols="12">
        <div class="d-table fill-height">
          <div
            class="d-table-cell grey lighten-4 pa-2 text-center"
            style="min-width:45px"
          >
            {{ item[1] }}
          </div>
          <v-divider class="d-table-cell" vertical></v-divider>
          <div class="d-table-cell pa-2">{{ item[0] }}</div>
        </div>
      </v-col>
    </v-row>
  </div>
</template>

<script>
export default {
  name: "PreviewItem",
  props: ["item"]
};
</script>
