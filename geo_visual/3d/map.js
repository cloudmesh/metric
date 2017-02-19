var dataUrl = 'https://raw.githubusercontent.com/cloudmesh/metric/master/geo_visual/data-coords.csv';
var symbolColor = 'yellow';
var basemap = 'dark-gray';
var proxy = 'raw.githubusercontent.com';

require([
  "esri/Map",
  "esri/views/SceneView",
  "esri/layers/CSVLayer",
  "esri/renderers/SimpleRenderer",
  "esri/symbols/PointSymbol3D",
  "esri/symbols/ObjectSymbol3DLayer",
  "esri/symbols/TextSymbol3DLayer",
  "esri/symbols/LabelSymbol3D",
  "esri/layers/support/LabelClass",
  "esri/config",
  "dojo/on",
  "dojo/dom",
  "dojo/domReady!"
], function(
  Map, SceneView, CSVLayer, SimpleRenderer, PointSymbol3D,
  ObjectSymbol3DLayer, TextSymbol3DLayer,
  LabelSymbol3D, LabelClass, esriConfig, on, dom
) {

  var objectSymbol,
    objectSymbolRenderer, csvLayer, labelClass;

  // Create the Map
  var map = new Map({
    basemap: basemap
  });

  // Create the SceneView and set initial camera
  var view = new SceneView({
    container: "viewDiv",
    map: map,
    camera: {
      position: [-98, 20, 2500000],
      tilt: 30,
      zoom: 3
    }
  });

  // Create objectSymbol and add to renderer
  objectSymbol = new PointSymbol3D({
    symbolLayers: [new ObjectSymbol3DLayer({
      width: 25000,
      resource: {
        primitive: "cube"
      },
      material: {
        color: symbolColor
      }  
    })]
  });
  objectSymbolRenderer = new SimpleRenderer({
    symbol: objectSymbol,
    visualVariables: [{
      type: "size",
      field: "# of Pubs",
      stops: [
        {
          value: 1,
          size: 1000
        },
        {
          value: 500,
          size: 1000000
        }]
    }, {
      type: "size",
      axis: "width-and-depth",
      useSymbolValue: true
    }]
  });

  labelClass = new LabelClass({
    symbol: new LabelSymbol3D({
      symbolLayers: [new TextSymbol3DLayer({
        material: {
          color: "white"
        },
        size: 10
      })]
    }),
    labelPlacement: "above-right",
    labelExpressionInfo: {
      value: "{Organization}"
    }
  });
  
  esriConfig.request.corsEnabledServers.push(proxy);
    
  csvLayer = new CSVLayer({
    url: dataUrl,
    renderer: objectSymbolRenderer,
    popupTemplate: popupTemplate,
    longitudeField: 'location_longitude',
    latitudeField: 'location_latitude',
    maxScale: 0,
    minScale: 0,
    labelsVisible: true,
    labelingInfo: [labelClass]
  });
  
  var popupTemplate = {
    title: '{Organization}',
    content: 'Number of publications: {# of Pubs}'
  };
  
  csvLayer.popupTemplate = popupTemplate;
  
  map.add(csvLayer);
});
