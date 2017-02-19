var map = Highcharts.maps['countries/us/us-all'];
var chart;
    
Highcharts.data({
    googleSpreadsheetKey: '1HiakX48K_7LvPk6a0eCOjHfjQj0PnJgqDVmNMaiOj1c',
    
    parsed: function(columns){
        var metricSelect = document.getElementById('metricSelect');
        for(var i = 1, max = columns.length; i < max; i++){
    		if(! columns[i][0].startsWith('location_')){
                  var option = document.createElement('option');
                  option.text = columns[i][0];
                  metricSelect.add(option);
            }
        }
        
        metricSelect.addEventListener("change", function(evt){
            selected = metricSelect.options[metricSelect.selectedIndex].text;
            data = scrubData(columns, keyName(selected));
            chart.series[2].setData(data, true);
            chart.series[2].update({tooltip: {pointFormat: '{point.organization}<br>' + selected + ': {point.z}'}});
            chart.setTitle({text: selected});
        });
        
        var metric = metricSelect.options[metricSelect.selectedIndex].text;
        
        var data = scrubData(columns, metric);

        chart = Highcharts.mapChart('container', {
            title: {
                text: metric
            },
            
            mapNavigation: {
                enabled: true
            },

            series: [{
                name: 'Basemap',
                mapData: map,
                borderColor: '#606060',
                nullColor: 'rgba(200, 200, 200, 0.2)',
                showInLegend: false
            }, {
                name: 'Separators',
                type: 'mapline',
                data: Highcharts.geojson(map, 'mapline'),
                color: '#101010',
                enableMouseTracking: false,
                showInLegend: false
            }, {
                tooltip: {
                    pointFormat: '{point.organization}<br>' + metric + ': {point.z}'
                },
                type: 'mapbubble',
                name: 'Organizations',
                data: data,
                maxSize: '12%',
                color: Highcharts.getOptions().colors[0]
            }]
        });
    }
});

/**
 * generates map data with 'z' variable, based on chosen metric
 * @param {Array} columns
 * @param {String} metric
 * @return {Object} data
 */
function scrubData(columns, metric){
    var data = [];
    for(var i = 1, rows = columns[0].length; i < rows; i++){
        obj = {}
        
        for(var j = 0, cols = columns.length; j < cols; j++){
            key = keyName(columns[j][0]);
            value = columns[j][i];

            if(key == keyName(metric)){
                obj['z'] = value;
            } else if(key == 'location_latitude') {
                obj['lat'] = value;
            } else if(key == 'location_longitude') {
                obj['lon'] = value;
            } else{
                obj[key] = value;
            }
        }
        
        if(obj['lat'] && obj['lon']){
            data.push(obj);
        }
    }
    
    return data;
}

/**
 * modifies metric to be useable with dot notation
 * @param {String} key
 * @return {String}
 */
function keyName(key){
    return key.replace('#', 'number').replace(/\s/g, '_').toLowerCase();   
};
