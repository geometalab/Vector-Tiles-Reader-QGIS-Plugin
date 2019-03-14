<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="2.18.13" simplifyAlgorithm="0" minimumScale="0" maximumScale="1e+08" simplifyDrawingHints="1" minLabelScale="0" maxLabelScale="1e+08" simplifyDrawingTol="1" readOnly="0" simplifyMaxScale="1" hasScaleBasedVisibilityFlag="0" simplifyLocal="1" scaleBasedLabelVisibilityFlag="0">
  <edittypes>
    <edittype widgetv2type="TextEdit" name="admin_level">
      <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
    </edittype>
    <edittype widgetv2type="TextEdit" name="disputed">
      <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
    </edittype>
    <edittype widgetv2type="TextEdit" name="_zoom">
      <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
    </edittype>
    <edittype widgetv2type="TextEdit" name="maritime">
      <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
    </edittype>
    <edittype widgetv2type="TextEdit" name="_row">
      <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
    </edittype>
    <edittype widgetv2type="TextEdit" name="_col">
      <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
    </edittype>
  </edittypes>
  <renderer-v2 forceraster="0" symbollevels="0" type="RuleRenderer" enableorderby="0">
    <rules key="06883f37-9772-4a2b-9978-e18f0774ead8">
      <rule scalemaxdenom="50000000" description="boundary-land-level-4-zoom-4" filter="((&quot;admin_level&quot; is not null and &quot;admin_level&quot; in ('4', '6', '8'))) and (&quot;maritime&quot; is null or &quot;maritime&quot; != '1')" key="{e1e045b2-6c32-40fb-a6b9-8e8bb5e450e3}" symbol="0" scalemindenom="100000" label="boundary-land-level-4-zoom-4§"/>
      <rule scalemaxdenom="25000000" description="boundary-land-level-4-zoom-5" filter="((&quot;admin_level&quot; is not null and &quot;admin_level&quot; in ('4', '6', '8'))) and (&quot;maritime&quot; is null or &quot;maritime&quot; != '1')" key="{d9de1327-88d1-4aed-a641-5f753880bdc7}" symbol="1" scalemindenom="1" label="boundary-land-level-4-zoom-5"/>
      <rule scalemaxdenom="1000000000" description="boundary-land-level-2-zoom-0" filter="(&quot;admin_level&quot; is not null and &quot;admin_level&quot; = '2') and (&quot;maritime&quot; is null or &quot;maritime&quot; != '1') and (&quot;disputed&quot; is null or &quot;disputed&quot; != '1')" key="{f965438e-7352-428f-af45-5c65615e0cdb}" symbol="2" scalemindenom="50000000" label="boundary-land-level-2-zoom-0"/>
      <rule scalemaxdenom="50000000" description="boundary-land-level-2-zoom-4" filter="(&quot;admin_level&quot; is not null and &quot;admin_level&quot; = '2') and (&quot;maritime&quot; is null or &quot;maritime&quot; != '1') and (&quot;disputed&quot; is null or &quot;disputed&quot; != '1')" key="{8ce117e2-b370-4dc3-880c-66503cdc379e}" symbol="3" scalemindenom="25000000" label="boundary-land-level-2-zoom-4"/>
      <rule scalemaxdenom="25000000" description="boundary-land-level-2-zoom-5" filter="(&quot;admin_level&quot; is not null and &quot;admin_level&quot; = '2') and (&quot;maritime&quot; is null or &quot;maritime&quot; != '1') and (&quot;disputed&quot; is null or &quot;disputed&quot; != '1')" key="{2bdae10d-5623-45c8-b119-b0fc6854ec39}" symbol="4" scalemindenom="1" label="boundary-land-level-2-zoom-5"/>
      <rule scalemaxdenom="1000000000" description="boundary-land-disputed-zoom-0" filter="(&quot;maritime&quot; is null or &quot;maritime&quot; != '1') and (&quot;disputed&quot; is not null and &quot;disputed&quot; = '1')" key="{3be4a6d8-ec6e-43f4-8cd7-01d24c7f1491}" symbol="5" scalemindenom="50000000" label="boundary-land-disputed-zoom-0"/>
      <rule scalemaxdenom="50000000" description="boundary-land-disputed-zoom-4" filter="(&quot;maritime&quot; is null or &quot;maritime&quot; != '1') and (&quot;disputed&quot; is not null and &quot;disputed&quot; = '1')" key="{b66ffba7-b045-44e2-9cb5-d18acae2dddc}" symbol="6" scalemindenom="25000000" label="boundary-land-disputed-zoom-4"/>
      <rule scalemaxdenom="25000000" description="boundary-land-disputed-zoom-5" filter="(&quot;maritime&quot; is null or &quot;maritime&quot; != '1') and (&quot;disputed&quot; is not null and &quot;disputed&quot; = '1')" key="{c7944081-1090-4d62-91cc-cabee5827e18}" symbol="7" scalemindenom="1" label="boundary-land-disputed-zoom-5"/>
      <rule scalemaxdenom="1000000000" description="boundary-water-zoom-0" filter="((&quot;admin_level&quot; is not null and &quot;admin_level&quot; in ('2', '4'))) and (&quot;maritime&quot; is not null and &quot;maritime&quot; = '1')" key="{7ba28c0f-4ac0-4031-b164-0a6b51ccdf25}" symbol="8" scalemindenom="50000000" label="boundary-water-zoom-0"/>
      <rule scalemaxdenom="50000000" description="boundary-water-zoom-4" filter="((&quot;admin_level&quot; is not null and &quot;admin_level&quot; in ('2', '4'))) and (&quot;maritime&quot; is not null and &quot;maritime&quot; = '1')" key="{5d8b204a-a3cb-49dc-a4df-112218dd8772}" symbol="9" scalemindenom="25000000" label="boundary-water-zoom-4"/>
      <rule scalemaxdenom="25000000" description="boundary-water-zoom-5" filter="((&quot;admin_level&quot; is not null and &quot;admin_level&quot; in ('2', '4'))) and (&quot;maritime&quot; is not null and &quot;maritime&quot; = '1')" key="{9e8c0d86-bec2-435b-b351-aaa8e59bb3d3}" symbol="10" scalemindenom="12500000" label="boundary-water-zoom-5"/>
      <rule scalemaxdenom="12500000" description="boundary-water-zoom-6" filter="((&quot;admin_level&quot; is not null and &quot;admin_level&quot; in ('2', '4'))) and (&quot;maritime&quot; is not null and &quot;maritime&quot; = '1')" key="{3e8ba0a2-eca3-4dcb-ae26-9b2026f2d7de}" symbol="11" scalemindenom="750000" label="boundary-water-zoom-6"/>
      <rule scalemaxdenom="750000" description="boundary-water-zoom-10" filter="((&quot;admin_level&quot; is not null and &quot;admin_level&quot; in ('2', '4'))) and (&quot;maritime&quot; is not null and &quot;maritime&quot; = '1')" key="{4175a135-f246-40b9-b223-7000c6408cc6}" symbol="12" scalemindenom="1" label="boundary-water-zoom-10"/>
    </rules>
    <symbols>
      <symbol alpha="1" clip_to_extent="1" type="line" name="0">
        <layer pass="0" class="SimpleLine" locked="0">
          <prop k="capstyle" v="round"/>
          <prop k="customdash" v="0;0"/>
          <prop k="customdash_dd_active" v="1"/>
          <prop k="customdash_dd_expression" v="concat((3 * 1), ';', ((1 * 1) + 1))"/>
          <prop k="customdash_dd_field" v=""/>
          <prop k="customdash_dd_useexpr" v="1"/>
          <prop k="customdash_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="customdash_unit" v="Pixel"/>
          <prop k="draw_inside_polygon" v="0"/>
          <prop k="joinstyle" v="round"/>
          <prop k="line_color" v="158,156,171,255"/>
          <prop k="line_style" v="solid"/>
          <prop k="line_width" v="1"/>
          <prop k="line_width_unit" v="Pixel"/>
          <prop k="offset" v="0"/>
          <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="offset_unit" v="Pixel"/>
          <prop k="use_custom_dash" v="1"/>
          <prop k="width_dd_active" v="1"/>
          <prop k="width_dd_expression" v="interpolate_exp(get_zoom_for_scale(@map_scale), 1.4, 4, 5, 0.4, 1)"/>
          <prop k="width_dd_field" v=""/>
          <prop k="width_dd_useexpr" v="1"/>
          <prop k="width_map_unit_scale" v="0,0,0,0,0,0"/>
        </layer>
      </symbol>
      <symbol alpha="1" clip_to_extent="1" type="line" name="1">
        <layer pass="0" class="SimpleLine" locked="0">
          <prop k="capstyle" v="round"/>
          <prop k="customdash" v="11;22"/>
          <prop k="customdash_dd_active" v="0"/>
          <prop k="customdash_dd_expression" v="concat((3 * 1), ';', ((1 * 1) + 1))"/>
          <prop k="customdash_dd_field" v=""/>
          <prop k="customdash_dd_useexpr" v="1"/>
          <prop k="customdash_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="customdash_unit" v="Pixel"/>
          <prop k="draw_inside_polygon" v="0"/>
          <prop k="joinstyle" v="round"/>
          <prop k="line_color" v="158,156,171,255"/>
          <prop k="line_style" v="solid"/>
          <prop k="line_width" v="1"/>
          <prop k="line_width_unit" v="Pixel"/>
          <prop k="offset" v="0"/>
          <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="offset_unit" v="Pixel"/>
          <prop k="use_custom_dash" v="1"/>
          <prop k="width_dd_active" v="1"/>
          <prop k="width_dd_expression" v="interpolate_exp(get_zoom_for_scale(@map_scale), 1.4, 5, 12, 1, 3)"/>
          <prop k="width_dd_field" v=""/>
          <prop k="width_dd_useexpr" v="1"/>
          <prop k="width_map_unit_scale" v="0,0,0,0,0,0"/>
        </layer>
      </symbol>
      <symbol alpha="0.6" clip_to_extent="1" type="line" name="10">
        <layer pass="0" class="SimpleLine" locked="0">
          <prop k="capstyle" v="round"/>
          <prop k="customdash" v="0;0"/>
          <prop k="customdash_dd_active" v="1"/>
          <prop k="customdash_dd_expression" v=""/>
          <prop k="customdash_dd_field" v=""/>
          <prop k="customdash_dd_useexpr" v="0"/>
          <prop k="customdash_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="customdash_unit" v="Pixel"/>
          <prop k="draw_inside_polygon" v="0"/>
          <prop k="joinstyle" v="round"/>
          <prop k="line_color" v="154,189,214,255"/>
          <prop k="line_style" v="solid"/>
          <prop k="line_width" v="1"/>
          <prop k="line_width_unit" v="Pixel"/>
          <prop k="offset" v="0"/>
          <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="offset_unit" v="Pixel"/>
          <prop k="use_custom_dash" v="0"/>
          <prop k="width_dd_active" v="1"/>
          <prop k="width_dd_expression" v="interpolate_exp(get_zoom_for_scale(@map_scale), 1, 5, 12, 2, 8)"/>
          <prop k="width_dd_field" v=""/>
          <prop k="width_dd_useexpr" v="1"/>
          <prop k="width_map_unit_scale" v="0,0,0,0,0,0"/>
        </layer>
      </symbol>
      <symbol alpha="0.6" clip_to_extent="1" type="line" name="11">
        <layer pass="0" class="SimpleLine" locked="0">
          <prop k="capstyle" v="round"/>
          <prop k="customdash" v="0;0"/>
          <prop k="customdash_dd_active" v="1"/>
          <prop k="customdash_dd_expression" v=""/>
          <prop k="customdash_dd_field" v=""/>
          <prop k="customdash_dd_useexpr" v="0"/>
          <prop k="customdash_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="customdash_unit" v="Pixel"/>
          <prop k="draw_inside_polygon" v="0"/>
          <prop k="joinstyle" v="round"/>
          <prop k="line_color" v="154,189,214,255"/>
          <prop k="line_style" v="solid"/>
          <prop k="line_width" v="1"/>
          <prop k="line_width_unit" v="Pixel"/>
          <prop k="offset" v="0"/>
          <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="offset_unit" v="Pixel"/>
          <prop k="use_custom_dash" v="0"/>
          <prop k="width_dd_active" v="1"/>
          <prop k="width_dd_expression" v="interpolate_exp(get_zoom_for_scale(@map_scale), 1, 5, 12, 2, 8)"/>
          <prop k="width_dd_field" v=""/>
          <prop k="width_dd_useexpr" v="1"/>
          <prop k="width_map_unit_scale" v="0,0,0,0,0,0"/>
        </layer>
      </symbol>
      <symbol alpha="1" clip_to_extent="1" type="line" name="12">
        <layer pass="0" class="SimpleLine" locked="0">
          <prop k="capstyle" v="round"/>
          <prop k="customdash" v="0;0"/>
          <prop k="customdash_dd_active" v="1"/>
          <prop k="customdash_dd_expression" v=""/>
          <prop k="customdash_dd_field" v=""/>
          <prop k="customdash_dd_useexpr" v="0"/>
          <prop k="customdash_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="customdash_unit" v="Pixel"/>
          <prop k="draw_inside_polygon" v="0"/>
          <prop k="joinstyle" v="round"/>
          <prop k="line_color" v="154,189,214,255"/>
          <prop k="line_style" v="solid"/>
          <prop k="line_width" v="1"/>
          <prop k="line_width_unit" v="Pixel"/>
          <prop k="offset" v="0"/>
          <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="offset_unit" v="Pixel"/>
          <prop k="use_custom_dash" v="0"/>
          <prop k="width_dd_active" v="1"/>
          <prop k="width_dd_expression" v="interpolate_exp(get_zoom_for_scale(@map_scale), 1, 5, 12, 2, 8)"/>
          <prop k="width_dd_field" v=""/>
          <prop k="width_dd_useexpr" v="1"/>
          <prop k="width_map_unit_scale" v="0,0,0,0,0,0"/>
        </layer>
      </symbol>
      <symbol alpha="1" clip_to_extent="1" type="line" name="2">
        <layer pass="0" class="SimpleLine" locked="0">
          <prop k="capstyle" v="round"/>
          <prop k="customdash" v="0;0"/>
          <prop k="customdash_dd_active" v="1"/>
          <prop k="customdash_dd_expression" v=""/>
          <prop k="customdash_dd_field" v=""/>
          <prop k="customdash_dd_useexpr" v="0"/>
          <prop k="customdash_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="customdash_unit" v="Pixel"/>
          <prop k="draw_inside_polygon" v="0"/>
          <prop k="joinstyle" v="round"/>
          <prop k="line_color" v="164,162,174,255"/>
          <prop k="line_style" v="solid"/>
          <prop k="line_width" v="1"/>
          <prop k="line_width_unit" v="Pixel"/>
          <prop k="offset" v="0"/>
          <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="offset_unit" v="Pixel"/>
          <prop k="use_custom_dash" v="0"/>
          <prop k="width_dd_active" v="1"/>
          <prop k="width_dd_expression" v="interpolate_exp(get_zoom_for_scale(@map_scale), 1, 0, 4, 0.6, 1.4)"/>
          <prop k="width_dd_field" v=""/>
          <prop k="width_dd_useexpr" v="1"/>
          <prop k="width_map_unit_scale" v="0,0,0,0,0,0"/>
        </layer>
      </symbol>
      <symbol alpha="1" clip_to_extent="1" type="line" name="3">
        <layer pass="0" class="SimpleLine" locked="0">
          <prop k="capstyle" v="round"/>
          <prop k="customdash" v="0;0"/>
          <prop k="customdash_dd_active" v="1"/>
          <prop k="customdash_dd_expression" v=""/>
          <prop k="customdash_dd_field" v=""/>
          <prop k="customdash_dd_useexpr" v="0"/>
          <prop k="customdash_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="customdash_unit" v="Pixel"/>
          <prop k="draw_inside_polygon" v="0"/>
          <prop k="joinstyle" v="round"/>
          <prop k="line_color" v="164,162,174,255"/>
          <prop k="line_style" v="solid"/>
          <prop k="line_width" v="1"/>
          <prop k="line_width_unit" v="Pixel"/>
          <prop k="offset" v="0"/>
          <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="offset_unit" v="Pixel"/>
          <prop k="use_custom_dash" v="0"/>
          <prop k="width_dd_active" v="1"/>
          <prop k="width_dd_expression" v="interpolate_exp(get_zoom_for_scale(@map_scale), 1, 4, 5, 1.4, 2)"/>
          <prop k="width_dd_field" v=""/>
          <prop k="width_dd_useexpr" v="1"/>
          <prop k="width_map_unit_scale" v="0,0,0,0,0,0"/>
        </layer>
      </symbol>
      <symbol alpha="1" clip_to_extent="1" type="line" name="4">
        <layer pass="0" class="SimpleLine" locked="0">
          <prop k="capstyle" v="round"/>
          <prop k="customdash" v="0;0"/>
          <prop k="customdash_dd_active" v="1"/>
          <prop k="customdash_dd_expression" v=""/>
          <prop k="customdash_dd_field" v=""/>
          <prop k="customdash_dd_useexpr" v="0"/>
          <prop k="customdash_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="customdash_unit" v="Pixel"/>
          <prop k="draw_inside_polygon" v="0"/>
          <prop k="joinstyle" v="round"/>
          <prop k="line_color" v="164,162,174,255"/>
          <prop k="line_style" v="solid"/>
          <prop k="line_width" v="1"/>
          <prop k="line_width_unit" v="Pixel"/>
          <prop k="offset" v="0"/>
          <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="offset_unit" v="Pixel"/>
          <prop k="use_custom_dash" v="0"/>
          <prop k="width_dd_active" v="1"/>
          <prop k="width_dd_expression" v="interpolate_exp(get_zoom_for_scale(@map_scale), 1, 5, 12, 2, 8)"/>
          <prop k="width_dd_field" v=""/>
          <prop k="width_dd_useexpr" v="1"/>
          <prop k="width_map_unit_scale" v="0,0,0,0,0,0"/>
        </layer>
      </symbol>
      <symbol alpha="1" clip_to_extent="1" type="line" name="5">
        <layer pass="0" class="SimpleLine" locked="0">
          <prop k="capstyle" v="round"/>
          <prop k="customdash" v="0;0"/>
          <prop k="customdash_dd_active" v="1"/>
          <prop k="customdash_dd_expression" v="concat((1 * 1), ';', ((3 * 1) + 1))"/>
          <prop k="customdash_dd_field" v=""/>
          <prop k="customdash_dd_useexpr" v="1"/>
          <prop k="customdash_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="customdash_unit" v="Pixel"/>
          <prop k="draw_inside_polygon" v="0"/>
          <prop k="joinstyle" v="round"/>
          <prop k="line_color" v="175,173,184,255"/>
          <prop k="line_style" v="solid"/>
          <prop k="line_width" v="1"/>
          <prop k="line_width_unit" v="Pixel"/>
          <prop k="offset" v="0"/>
          <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="offset_unit" v="Pixel"/>
          <prop k="use_custom_dash" v="1"/>
          <prop k="width_dd_active" v="1"/>
          <prop k="width_dd_expression" v="interpolate_exp(get_zoom_for_scale(@map_scale), 1, 0, 4, 0.6, 1.4)"/>
          <prop k="width_dd_field" v=""/>
          <prop k="width_dd_useexpr" v="1"/>
          <prop k="width_map_unit_scale" v="0,0,0,0,0,0"/>
        </layer>
      </symbol>
      <symbol alpha="1" clip_to_extent="1" type="line" name="6">
        <layer pass="0" class="SimpleLine" locked="0">
          <prop k="capstyle" v="round"/>
          <prop k="customdash" v="0;0"/>
          <prop k="customdash_dd_active" v="1"/>
          <prop k="customdash_dd_expression" v="concat((1 * 1), ';', ((3 * 1) + 1))"/>
          <prop k="customdash_dd_field" v=""/>
          <prop k="customdash_dd_useexpr" v="1"/>
          <prop k="customdash_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="customdash_unit" v="Pixel"/>
          <prop k="draw_inside_polygon" v="0"/>
          <prop k="joinstyle" v="round"/>
          <prop k="line_color" v="175,173,184,255"/>
          <prop k="line_style" v="solid"/>
          <prop k="line_width" v="1"/>
          <prop k="line_width_unit" v="Pixel"/>
          <prop k="offset" v="0"/>
          <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="offset_unit" v="Pixel"/>
          <prop k="use_custom_dash" v="1"/>
          <prop k="width_dd_active" v="1"/>
          <prop k="width_dd_expression" v="interpolate_exp(get_zoom_for_scale(@map_scale), 1, 4, 5, 1.4, 2)"/>
          <prop k="width_dd_field" v=""/>
          <prop k="width_dd_useexpr" v="1"/>
          <prop k="width_map_unit_scale" v="0,0,0,0,0,0"/>
        </layer>
      </symbol>
      <symbol alpha="1" clip_to_extent="1" type="line" name="7">
        <layer pass="0" class="SimpleLine" locked="0">
          <prop k="capstyle" v="round"/>
          <prop k="customdash" v="0;0"/>
          <prop k="customdash_dd_active" v="1"/>
          <prop k="customdash_dd_expression" v="concat((1 * 1), ';', ((3 * 1) + 1))"/>
          <prop k="customdash_dd_field" v=""/>
          <prop k="customdash_dd_useexpr" v="1"/>
          <prop k="customdash_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="customdash_unit" v="Pixel"/>
          <prop k="draw_inside_polygon" v="0"/>
          <prop k="joinstyle" v="round"/>
          <prop k="line_color" v="175,173,184,255"/>
          <prop k="line_style" v="solid"/>
          <prop k="line_width" v="1"/>
          <prop k="line_width_unit" v="Pixel"/>
          <prop k="offset" v="0"/>
          <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="offset_unit" v="Pixel"/>
          <prop k="use_custom_dash" v="1"/>
          <prop k="width_dd_active" v="1"/>
          <prop k="width_dd_expression" v="interpolate_exp(get_zoom_for_scale(@map_scale), 1, 5, 12, 2, 8)"/>
          <prop k="width_dd_field" v=""/>
          <prop k="width_dd_useexpr" v="1"/>
          <prop k="width_map_unit_scale" v="0,0,0,0,0,0"/>
        </layer>
      </symbol>
      <symbol alpha="0.6" clip_to_extent="1" type="line" name="8">
        <layer pass="0" class="SimpleLine" locked="0">
          <prop k="capstyle" v="round"/>
          <prop k="customdash" v="0;0"/>
          <prop k="customdash_dd_active" v="1"/>
          <prop k="customdash_dd_expression" v=""/>
          <prop k="customdash_dd_field" v=""/>
          <prop k="customdash_dd_useexpr" v="0"/>
          <prop k="customdash_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="customdash_unit" v="Pixel"/>
          <prop k="draw_inside_polygon" v="0"/>
          <prop k="joinstyle" v="round"/>
          <prop k="line_color" v="154,189,214,255"/>
          <prop k="line_style" v="solid"/>
          <prop k="line_width" v="1"/>
          <prop k="line_width_unit" v="Pixel"/>
          <prop k="offset" v="0"/>
          <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="offset_unit" v="Pixel"/>
          <prop k="use_custom_dash" v="0"/>
          <prop k="width_dd_active" v="1"/>
          <prop k="width_dd_expression" v="interpolate_exp(get_zoom_for_scale(@map_scale), 1, 0, 4, 0.6, 1.4)"/>
          <prop k="width_dd_field" v=""/>
          <prop k="width_dd_useexpr" v="1"/>
          <prop k="width_map_unit_scale" v="0,0,0,0,0,0"/>
        </layer>
      </symbol>
      <symbol alpha="0.6" clip_to_extent="1" type="line" name="9">
        <layer pass="0" class="SimpleLine" locked="0">
          <prop k="capstyle" v="round"/>
          <prop k="customdash" v="0;0"/>
          <prop k="customdash_dd_active" v="1"/>
          <prop k="customdash_dd_expression" v=""/>
          <prop k="customdash_dd_field" v=""/>
          <prop k="customdash_dd_useexpr" v="0"/>
          <prop k="customdash_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="customdash_unit" v="Pixel"/>
          <prop k="draw_inside_polygon" v="0"/>
          <prop k="joinstyle" v="round"/>
          <prop k="line_color" v="154,189,214,255"/>
          <prop k="line_style" v="solid"/>
          <prop k="line_width" v="1"/>
          <prop k="line_width_unit" v="Pixel"/>
          <prop k="offset" v="0"/>
          <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="offset_unit" v="Pixel"/>
          <prop k="use_custom_dash" v="0"/>
          <prop k="width_dd_active" v="1"/>
          <prop k="width_dd_expression" v="interpolate_exp(get_zoom_for_scale(@map_scale), 1, 4, 5, 1.4, 2)"/>
          <prop k="width_dd_field" v=""/>
          <prop k="width_dd_useexpr" v="1"/>
          <prop k="width_map_unit_scale" v="0,0,0,0,0,0"/>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  <labeling type="rule-based">
    <rules key="{f5bc781f-6121-433c-b3ed-1f6780a53744}"/>
  </labeling>
  <customproperties>
    <property key="VectorTilesReader/geo_type" value="LineString"/>
    <property key="VectorTilesReader/is_empty" value="false"/>
    <property key="VectorTilesReader/layerStyle" value="c:\users\martin\appdata\local\temp\vector_tiles_reader\styles\OpenMapTiles.com (with custom key)\boundary.linestring.qml"/>
    <property key="VectorTilesReader/vector_tile_source" value="https://free.tilehosting.com/data/v3.json?key=6irhAXGgsi8TrIDL0211"/>
    <property key="VectorTilesReader/zoom_level" value="14"/>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerTransparency>0</layerTransparency>
  <displayfield>name</displayfield>
  <label>0</label>
  <labelattributes>
    <label fieldname="" text="Label"/>
    <family fieldname="" name="Cantarell"/>
    <size fieldname="" units="pt" value="12"/>
    <bold fieldname="" on="0"/>
    <italic fieldname="" on="0"/>
    <underline fieldname="" on="0"/>
    <strikeout fieldname="" on="0"/>
    <color fieldname="" red="0" blue="0" green="0"/>
    <x fieldname=""/>
    <y fieldname=""/>
    <offset x="0" y="0" units="pt" yfieldname="" xfieldname=""/>
    <angle fieldname="" value="0" auto="0"/>
    <alignment fieldname="" value="center"/>
    <buffercolor fieldname="" red="255" blue="255" green="255"/>
    <buffersize fieldname="" units="pt" value="1"/>
    <bufferenabled fieldname="" on=""/>
    <multilineenabled fieldname="" on=""/>
    <selectedonly on=""/>
  </labelattributes>
  <SingleCategoryDiagramRenderer diagramType="Histogram" sizeLegend="0" attributeLegend="1">
    <DiagramCategory penColor="#000000" labelPlacementMethod="XHeight" penWidth="0" diagramOrientation="Up" sizeScale="0,0,0,0,0,0" minimumSize="0" barWidth="5" penAlpha="255" maxScaleDenominator="25000" backgroundColor="#ffffff" transparency="0" width="15" scaleDependency="Area" backgroundAlpha="255" angleOffset="1440" scaleBasedVisibility="0" enabled="0" height="15" lineSizeScale="0,0,0,0,0,0" sizeType="MM" lineSizeType="MM" minScaleDenominator="inf">
      <fontProperties description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0" style=""/>
      <attribute field="" color="#000000" label=""/>
    </DiagramCategory>
    <symbol alpha="1" clip_to_extent="1" type="marker" name="sizeSymbol">
      <layer pass="0" class="SimpleMarker" locked="0">
        <prop k="angle" v="0"/>
        <prop k="color" v="255,0,0,255"/>
        <prop k="horizontal_anchor_point" v="1"/>
        <prop k="joinstyle" v="bevel"/>
        <prop k="name" v="circle"/>
        <prop k="offset" v="0,0"/>
        <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
        <prop k="offset_unit" v="MM"/>
        <prop k="outline_color" v="0,0,0,255"/>
        <prop k="outline_style" v="solid"/>
        <prop k="outline_width" v="0"/>
        <prop k="outline_width_map_unit_scale" v="0,0,0,0,0,0"/>
        <prop k="outline_width_unit" v="MM"/>
        <prop k="scale_method" v="diameter"/>
        <prop k="size" v="2"/>
        <prop k="size_map_unit_scale" v="0,0,0,0,0,0"/>
        <prop k="size_unit" v="MM"/>
        <prop k="vertical_anchor_point" v="1"/>
      </layer>
    </symbol>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings yPosColumn="-1" showColumn="-1" linePlacementFlags="10" placement="2" dist="0" xPosColumn="-1" priority="0" obstacle="0" zIndex="0" showAll="1"/>
  <annotationform>.</annotationform>
  <aliases>
    <alias field="admin_level" index="0" name=""/>
    <alias field="disputed" index="1" name=""/>
    <alias field="_zoom" index="2" name=""/>
    <alias field="maritime" index="3" name=""/>
    <alias field="_row" index="4" name=""/>
    <alias field="_col" index="5" name=""/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <attributeactions default="-1"/>
  <attributetableconfig actionWidgetStyle="dropDown" sortExpression="" sortOrder="0">
    <columns>
      <column width="-1" hidden="0" type="field" name="admin_level"/>
      <column width="-1" hidden="0" type="field" name="disputed"/>
      <column width="-1" hidden="0" type="field" name="_zoom"/>
      <column width="-1" hidden="0" type="field" name="maritime"/>
      <column width="-1" hidden="0" type="field" name="_row"/>
      <column width="-1" hidden="0" type="field" name="_col"/>
      <column width="-1" hidden="1" type="actions"/>
    </columns>
  </attributetableconfig>
  <editform>.</editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath>.</editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <widgets/>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <defaults>
    <default field="admin_level" expression=""/>
    <default field="disputed" expression=""/>
    <default field="_zoom" expression=""/>
    <default field="maritime" expression=""/>
    <default field="_row" expression=""/>
    <default field="_col" expression=""/>
  </defaults>
  <previewExpression></previewExpression>
  <layerGeometryType>1</layerGeometryType>
</qgis>
