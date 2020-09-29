<template>
  <div>
    <v-row justify="center" no-gutters>
      <v-col class="text-left" cols="6">
        <div class="d-table fill-height">
          <div class="d-table-cell grey lighten-5 pa-2 text-center font-weight-medium" style="min-width:45px">
            {{ parseInt(item.line_id) + 1 }}
          </div>
          <v-divider class="d-table-cell" vertical></v-divider>
          <div class="d-table-cell fill-width color-transition" :class="[{blue: changed_from},{'lighten-5': changed_from}]">
            <div class="pa-2">
              <div class="d-table fill-height fill-width">
                <div class="d-table-cell">
                  <v-textarea class="ta-custom" auto-grow rows=1 text-wrap @click.native.stop @keyup.space.prevent
                    @keydown.ctrl.83.prevent="$event.target.blur()"
                    @blur="editProcessing($event, item.line_id, 'from')" @input="onTextChange('from')"
                    :value="item.text">
                  </v-textarea>
                </div>
              </div>
            </div>
          </div>
        </div>
      </v-col>
      <v-col class="text-left" cols="6">
        <div class="d-table fill-height fill-width">
          <v-divider class="d-table-cell" vertical></v-divider>
          <div class="d-table-cell lighten-5 text-center" style="min-width:45px" :class="{
                grey: item.selected.sim <= 0.3,
                green: item.selected.sim > 0.5,
                yellow: (item.selected.sim <= 0.5) && (item.selected.sim > 0.3)
              }">
            <div class="fill-height lighten-5 d-flex flex-column justify-space-between">
              <div class="pa-2 font-weight-medium">
                {{ selectedLineId }}
              </div>
              <div class="text-caption pa-1">
                {{ item.selected.sim | numeral("0.00") }}
              </div>
            </div>
          </div>
          <v-divider class="d-table-cell" vertical></v-divider>
          <div class="d-table-cell fill-width color-transition"
            :class="[{blue: changed_to},{'lighten-5': changed_to}]">
            <div class="pa-2">
              <div class="d-table fill-height fill-width">
                <div class="d-table-cell">
                  <v-textarea class="ta-custom" auto-grow rows=1 text-wrap @click.native.stop @keyup.space.prevent
                    @keydown.ctrl.83.prevent="$event.target.blur()"
                    @blur="editProcessing($event, item.line_id, 'to')" @input="onTextChange('to')"
                    :value="item.selected.text">
                  </v-textarea>
                </div>
                <div class="d-table-cell" style="width:15px">
                  <i class="v-icon mdi mdi-chevron-down theme--light"
                    style="border-radius:50%; background:#f2f2f2; cursor:pointer;" @click="toggleShowLines"
                    :class="{'icon-avtive':showLines}"></i>
                </div>
              </div>
            </div>
            <!-- <v-expand-transition> -->
            <!-- <v-slide-y-transition group hide-on-leave> -->
            <!-- <div v-show="showLines"> -->
            <div v-for="(t,i) in linesTo" :key="i">
              <v-divider></v-divider>
              <div class="d-table fill-height fill-width">
                <div class="d-table-cell lighten-5 grey text-center font-weight-medium" style="min-width:45px">
                  <div class="fill-height lighten-5 d-flex flex-column justify-space-between">
                    <div class="pa-2 font-weight-medium">
                      {{ t.line_id + 1 }}
                    </div>
                    <div class="text-caption pa-1">
                      {{ t.sim | numeral("0.00") }}
                    </div>
                  </div>
                </div>
                <v-divider class="d-table-cell" vertical></v-divider>
                <div class="d-table-cell yellow pa-2 fill-width"
                  :class="[{'lighten-4': t.line_id==item.selected.line_id}, {'lighten-5': t.line_id!=item.selected.line_id}]">
                  {{ t.text }}
                </div>
              </div>
            </div>
            <!-- </div> -->
            <!-- </v-expand-transition> -->
            <!-- </v-slide-y-transition> -->
          </div>
        </div>
      </v-col>
    </v-row>
  </div>
</template>

<script>
  import {
    DEFAULT_VARIANTS_WINDOW_TO
  } from "@/common/config"
  import {
    STATE_SAVED,
    STATE_CHANGED,
    RESULT_OK
  } from "@/common/constants"
  export default {
    name: "EditItem",
    props: ["item", "collapse"],
    data() {
      return {
        state: STATE_SAVED,
        STATE_CHANGED,
        showLines: false,
        changed_from: false,
        changed_to: false
      }
    },
    methods: {
      editProcessing(event, line_id, text_type) {
        // event.target.value = event.target.value .replace(/(\r\n|\n|\r)/gm, "")
        this.$emit('editProcessing', line_id, event.target.value, text_type, (res) => {
          console.log("edit result:", res)
          if (res == RESULT_OK) {
            this.state = STATE_SAVED;
            this.changed_from = false;
            this.changed_to = false;
          } else {
            console.log("Edit error on save.")
          }
        })
      },
      onTextChange(text_type) {
        this.state = STATE_CHANGED
        if (text_type == "from") {
          this.changed_from = true;
        } else {
          this.changed_to = true;
        }
      },
      toggleShowLines() {
        this.showLines = !this.showLines;
      }
    },
    computed: {
      selectedLineId() {
        return parseInt(this.item.selected.line_id) + 1;
      },
      linesTo() {
        let sid = this.item.selected.line_id;
        let wnd = DEFAULT_VARIANTS_WINDOW_TO;
        // not working with loadash _ (v-for is hiding)
        if (this.showLines) {
          return this.item.trans.filter(function (tr) {
            return tr.line_id < sid + wnd && tr.line_id > sid - wnd
          }).sort((a, b) => (a.sim > b.sim) ? -1 : ((b.sim > a.sim) ? 1 : 0)).slice(0, 5);
        }
        return [];
      }
    },
    watch: {
      collapse: function () {
        this.showLines = false;
      }
    }
  };
</script>