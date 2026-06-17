<?php
/*
Plugin Name: MMM Game Embed
Description: Shortcode to embed the Abbey Island Mystery game via iframe. Usage: [mmm_game url="https://example.com/path/index.html" height="800px"]
Version: 0.1
Author: Generated
*/

if (!defined('ABSPATH')) {
  exit;
}

function mmm_game_shortcode($atts) {
  $a = shortcode_atts(array('url'=>'','width'=>'100%','height'=>'800px'), $atts);
  if (empty($a['url'])) return '<!-- mmm_game: no url provided -->';
  $url = esc_url($a['url']);
  $width = esc_attr($a['width']);
  $height = esc_attr($a['height']);
  return '<div class="mmm-game-embed" style="max-width:100%;"><iframe src="'. $url .'" width="'. $width .'" height="'. $height .'" style="border:0;width:100%;height:'. $height .';" loading="lazy" allow="fullscreen; autoplay"></iframe></div>';
}
add_shortcode('mmm_game','mmm_game_shortcode');
