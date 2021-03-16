<template>
  <v-dialog v-model="show" max-width="500px">
    <v-card>
      <v-card-title>
        Shift batch {{batch_id + 1}}
      </v-card-title>
      <!-- <v-card-text class="mt-5">
        Window shift
      </v-card-text> -->
      <v-card-actions class="px-15 mt-10 d-flex justify-space-between">
          <v-btn fab outlined color="gray" @click="shift-=stepSize">
            <v-icon>mdi-arrow-left</v-icon>
          </v-btn>
          <div class="text-h4">
            {{shift}}
          </div>
          <v-btn fab outlined color="gray" @click="shift+=stepSize">
            <v-icon>mdi-arrow-right</v-icon>
          </v-btn>
      </v-card-actions>
      <v-card-actions class="mt-10">
        <v-btn color="primary" text @click="show=false">
          Close
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn color="primary" dark @click="recalculateBatch">
          Recalculate
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
  export default {
    name: "RecalculateBatchDialog",
    props: {
      value: Boolean,
      batch_id: Number
    },
    data() {
      return {
        shift: 0,
        stepSize: 20
      }
    },
    methods: {
      recalculateBatch() {
        this.show = false;
        this.$emit('recalculateBatch', this.batch_id, this.shift)
      },
    },
    computed: {
      show: {
        get() {
          return this.value
        },
        set(value) {
          this.$emit('input', value)
        }
      }
    }
  }
</script>
