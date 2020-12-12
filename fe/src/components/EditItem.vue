<template>
  <div>
    <!-- <v-row justify="center" no-gutters>
      <v-col class="text-left grey lighten-4" cols="12">
        <div class="d-table fill-height">
          <div class="d-table-cell px-2 py-0 font-weight-bold text-caption">
            line {{ item.index_id + 1 }}
          </div>
          <div class="d-table-cell px-2 py-0 font-weight-bold text-caption grey--text d-flex">
            <div class="px-2">
              вставить
            </div>
            <div class="px-2">
              удалить
            </div>
          </div>
        </div>
      </v-col>
    </v-row> -->



    <!-- <v-divider></v-divider> -->


    <v-row justify="center" class="edit-row" no-gutters>

      <!-- line menu -->
      <div class="cell-top-menu">
          <div class="px-2 py-0 font-weight-bold text-caption d-flex">
            <div class="px-2 cell-top-menu-item" @click="editAddEmptyLineAfter()">
              + строка
            </div>
            <!-- ↑ ↓ -->
            <div class="px-2 cell-top-menu-item" @click="editDeleteLine()">
              удалить
            </div>
            <v-spacer></v-spacer>
            <div class="px-2 cell-top-menu-item">
              строка {{item.index_id + 1}}
            </div>
          </div>
      </div>

      <!-- left side -->
      <v-col class="text-left" cols="6">
        <div class="d-table fill-height">

          <!-- <div class="d-table-cell grey lighten-5 pa-2 text-center font-weight-medium cell-edit-to-index line-num">
            {{ lineIdFrom }}
          </div>
          <v-divider class="d-table-cell" vertical></v-divider> -->
          <div class="d-table-cell green lighten-5 cell-edit-to-index text-center">
            <div class="fill-height d-flex cell-edit-to-index-cont flex-column justify-space-between">
              <div class="pa-2 font-weight-medium line-num">
                {{ lineIdFrom }}
              </div>
              <div class="cell-edit-to-action-panel">
                <div class="cell-edit-button" @click="editAddUpEnd('from', item.text_from)"></div>
                <div class="cell-edit-button" @click="editAddDownEnd('from', item.text_from)"></div>
                <div class="cell-edit-button" @click="editClearLine('from')"></div>
                <!-- <div class="cell-edit-button"></div> -->
                <!-- <div class="cell-edit-button"></div> -->
              </div>
              <!-- <div class="text-caption pa-1">
                {{ item.selected.sim | numeral("0.00") }}
              </div> -->
            </div>
          </div>
          <v-divider class="d-table-cell" vertical></v-divider>
          <div class="d-table-cell fill-width color-transition" :class="[{blue: changed_from},{'lighten-5': changed_from}]">
            <div class="pa-2 pb-8">
              <div class="d-table fill-height fill-width">
                <div class="d-table-cell">
                  <v-textarea class="ta-custom" auto-grow rows=1 text-wrap placeholder="Write your text here"
                    @click.native.stop
                    @keyup.space.prevent
                    @keydown.ctrl.83.prevent="$event.target.blur()"
                    @focus="setUneditedText($event)"
                    @blur="editProcessing($event, 'from')"
                    @input="onTextChange('from')"
                    :value="item.text_from">
                  </v-textarea>
                </div>

                <div class="d-table-cell" style="width:15px">
                  <i class="v-icon mdi mdi-chevron-down theme--light"
                    style="border-radius:50%; background:#f2f2f2; cursor:pointer;" @click="toggleShowLines('from')"
                    :class="{'icon-avtive':showLinesFrom}"></i>
                </div>
              </div>
            </div>

            <!-- CANDIDATES LEFT BLOCK -->
            <div v-show="showLinesFrom">
              <div v-for="(t,i) in transFrom" :key="i">
                <v-divider></v-divider>
                <div class="d-table fill-height fill-width">
                  <div class="d-table-cell lighten-5 grey text-center font-weight-medium" style="min-width:45px">
                    <div class="fill-height lighten-5 d-flex flex-column justify-space-between">
                      <div class="pa-2 font-weight-medium">
                        {{ t.id }}
                      </div>

                      <!-- candidates similarity -->
                      <!-- <div class="text-caption pa-1">
                        {{ t.sim | numeral("0.00") }}
                      </div> -->
                    </div>
                  </div>
                  <v-divider class="d-table-cell" vertical></v-divider>
                  <div class="d-table-cell yellow pa-2 fill-width"
                    :class="[{'lighten-4': t.id==lineIdTo}, {'lighten-5': t.id!=lineIdTo}]">
                    {{ t.text }}
                    <!-- PROXY TRANSLATION CANDIDATES TEXT -->
                    <div v-if="showProxyTo == 'true' && t.proxy" class="mt-4 proxy-to-cand-subtitles font-weight-medium">  
                      {{t.proxy}}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
          </div>
        </div>
      </v-col>
      <!-- right side -->
      <v-col class="text-left" cols="6">
        <div class="d-table fill-height fill-width cell-edit-to">

          <v-divider class="d-table-cell" vertical></v-divider>
          <!-- <div class="d-table-cell lighten-5 text-center" style="min-width:45px" :class="{
                grey: item.selected.sim <= 0.3,
                green: item.selected.sim > 0.5,
                yellow: (item.selected.sim <= 0.5) && (item.selected.sim > 0.3)
              }"> -->
          <div class="d-table-cell green lighten-5 cell-edit-to-index text-center">
            <div class="fill-height d-flex cell-edit-to-index-cont flex-column justify-space-between">
              <div class="pa-2 font-weight-medium line-num">
                {{ lineIdTo }}
              </div>
              <div class="cell-edit-to-action-panel">
                <div class="cell-edit-button" @click="editAddUpEnd('to', item.text_to)"></div>
                <div class="cell-edit-button" @click="editAddDownEnd('to', item.text_to)"></div>
                <div class="cell-edit-button" @click="editClearLine('to')"></div>
                <!-- <div class="cell-edit-button"></div> -->
                <!-- <div class="cell-edit-button"></div> -->
              </div>
              <!-- <div class="text-caption pa-1">
                {{ item.selected.sim | numeral("0.00") }}
              </div> -->
            </div>
          </div>
          
          <v-divider class="d-table-cell" vertical></v-divider>

          <div class="d-table-cell fill-width color-transition"
            :class="[{blue: changed_to},{'lighten-5': changed_to}]">
            <div class="pa-2 pb-8">
              <div class="d-table fill-height fill-width">
                <div class="d-table-cell">
                  <v-textarea class="ta-custom" auto-grow rows=1 text-wrap placeholder="Write your text here"
                    @click.native.stop
                    @keyup.space.prevent
                    @keydown.ctrl.83.prevent="$event.target.blur()"
                    @focus="setUneditedText($event)"
                    @blur="editProcessing($event, 'to')"
                    @input="onTextChange('to')"
                    :value="item.text_to">
                  </v-textarea>
                  <!-- prevItemLineId {{prevSelectedLineId}} -->
                  <!-- PROXY TRANSLATION TEXT -->
                  <div v-if="showProxyTo == 'true' && item.proxy_to" class="mt-3 proxy-to-subtitles grey lighten-3 font-weight-medium">  
                    {{item.proxy_to}}
                  </div>
                </div>
                <div class="d-table-cell" style="width:15px">
                  <i class="v-icon mdi mdi-chevron-down theme--light"
                    style="border-radius:50%; background:#f2f2f2; cursor:pointer;" @click="toggleShowLines('to')"
                    :class="{'icon-avtive':showLines}"></i>
                </div>
              </div>
            </div>

            <!-- CANDIDATES RIGHT BLOCK -->

            <!-- candidates animation -->
            <!-- <v-expand-transition> -->
            <!-- <v-slide-y-transition group hide-on-leave> -->
            <div v-show="showLines">
              <div v-for="(t,i) in trans" :key="i">
                <v-divider></v-divider>
                <div class="d-table fill-height fill-width">
                  <div class="d-table-cell lighten-5 grey text-center font-weight-medium" style="min-width:45px">
                    <div class="fill-height lighten-5 d-flex flex-column justify-space-between">
                      <div class="pa-2 font-weight-medium">
                        {{ t.id }}
                      </div>

                      <!-- candidates similarity -->
                      <!-- <div class="text-caption pa-1">
                        {{ t.sim | numeral("0.00") }}
                      </div> -->
                    </div>
                  </div>
                  <v-divider class="d-table-cell" vertical></v-divider>
                  <div class="d-table-cell yellow pa-2 fill-width"
                    :class="[{'lighten-4': t.id==lineIdTo}, {'lighten-5': t.id!=lineIdTo}]">
                    {{ t.text }}
                    <!-- PROXY TRANSLATION CANDIDATES TEXT -->
                    <div v-if="showProxyTo == 'true' && t.proxy" class="mt-4 proxy-to-cand-subtitles font-weight-medium">  
                      {{t.proxy}}
                    </div>
                  </div>
                </div>
              </div>
            </div>
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
    // DEFAULT_VARIANTS_WINDOW_TO
  } from "@/common/config"
  import {
    STATE_SAVED,
    STATE_CHANGED,
    RESULT_OK
  } from "@/common/constants"
  import {
    Helper
  } from "@/common/helper"
  export default {
    name: "EditItem",
    props: ["item", "collapse", "clearCandidates", "showProxyTo", "prevItem", "fileId", ],
    data() {
      return {
        state: STATE_SAVED,
        STATE_CHANGED,
        showLines: false,
        showLinesFrom: false,
        changed_from: false,
        changed_to: false,
        uneditedText: null,
        trans: [],
        transFrom: []
      }
    },
    methods: {
      getCandidates(textType) {
        this.$emit('getCandidates', this.item.index_id, textType, 2, 5, (res, data) => {
          if (res == RESULT_OK) {
              console.log("getCandidates", data.items)
              if (textType=="from") {
                this.transFrom = data.items;
              } else if (textType=="to") {
                this.trans = data.items;
              }
            } else {
              console.log("Edit error on getCandidates.")
            }
        });
      },
      editAddUpEnd(textType, text) {
        this.$emit('editAddUpEnd', this.item.index_id, text, textType, (res) => {
          if (res == RESULT_OK) {
              console.log("editAddUpEnd OK")
              //обновляем предыдущий элемент
            } else {
              console.log("Edit error on editAddUpEnd.")
            }
        });
      },
      editAddDownEnd(textType, text) {
        this.$emit('editAddDownEnd', this.item.index_id, text, textType, (res) => {
          if (res == RESULT_OK) {
              console.log("editAddDownEnd OK")
            } else {
              console.log("Edit error on editAddDownEnd.")
            }
        });
      },
      editDeleteLine() {
        this.$emit('editDeleteLine', this.item.index_id);
      },
      editAddEmptyLineBefore() {
        this.$emit('editAddEmptyLineBefore', this.item.index_id);
      },
      editAddEmptyLineAfter() {
        this.$emit('editAddEmptyLineAfter', this.item.index_id);
      },
      editClearLine(textType) {
        this.$emit('editClearLine', this.item.index_id, textType);
      },
      editProcessing(event, textType) {
        // event.target.value = event.target.value .replace(/(\r\n|\n|\r)/gm, "")

        // #Не сохранять, если не изменилось
        let newText = event.target.value;
        if (Helper.trim(newText) != Helper.trim(this.uneditedText)) {
          this.$emit('editProcessing', this.item.index_id, newText, textType, (res) => {
            console.log("edit result:", res)
            if (res == RESULT_OK) {
              this.state = STATE_SAVED;
              this.changed_from = false;
              this.changed_to = false;
            } else {
              console.log("Edit error on save.")
            }
          });
        }
      },
      setUneditedText(event) {
        this.uneditedText = event.target.value;
      },
      onTextChange(text_type) {
        this.state = STATE_CHANGED
        if (text_type == "from") {
          this.changed_from = true;
        } else {
          this.changed_to = true;
        }
      },
      toggleShowLines(textType) {
        if (textType=="from") {
          this.showLinesFrom = !this.showLinesFrom;
          if (this.transFrom.length == 0) {
            this.getCandidates(textType);
          }
        } else if (textType=="to") {
          this.showLines = !this.showLines;
          if (this.trans.length == 0) {
            this.getCandidates(textType);
          }
        }
      }
    },
    computed: {
      lineIdFrom() {
        return JSON.parse(this.item.line_id_from).map(function(num) { return num }).join(", ");
      },
      lineIdTo() {
        return JSON.parse(this.item.line_id_to).map(function(num) { return num }).join(", ");
      },
      prevLineIdTo() {
        //correct
        return JSON.parse(this.prevItem.line_id_to)[0];
      },
      linesTo() {
        // let sid = this.item.selected.line_id;
        // let wnd = DEFAULT_VARIANTS_WINDOW_TO;
        // let wnd = 5;
        // not working with loadash _ (v-for is hiding)

        // let prevLineId = this.prevLineIdTo;
        // console.log("line_id:", this.selectedLineId, "prev_line_id:", prevLineId, DEFAULT_VARIANTS_WINDOW_TO)

        // if (this.showLines) {
        //   return this.item.trans.filter(function (tr) {

        //     return tr.processing_to_id >= prevLineId;
        //     // return tr.line_id < sid + wnd && tr.line_id > sid - wnd;
        //   })
          
        //   //sort by similarity
        //   // }).sort((a, b) => (a.sim > b.sim) ? -1 : ((b.sim > a.sim) ? 1 : 0))

        //   //get top values
        //   .slice(0, 5);
        // }

        return this.item.trans;

        // return [];
      }
    },
    watch: {
      collapse: function () {
        this.showLines = false;
      },
      clearCandidates: function () {
        this.trans = [];
        this.transFrom = [];
        this.showLines = false;
        this.showLinesFrom = false;
      }
    }
  };
</script>