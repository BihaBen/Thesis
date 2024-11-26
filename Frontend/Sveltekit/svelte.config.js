import preprocess from 'svelte-preprocess';

export default {
  preprocess: preprocess(),
  kit: {
    alias: {
      $lib: 'src/lib'
    }
  }
};
