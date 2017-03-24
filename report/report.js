$(function() {
    var series = [{
        name: 'Publication Type Percentage',
        data: [
            {name:'Journal Paper', y:6321},
            {name:'None', y:3266},
            {name:'Conference Paper', y:492},
            {name:'Book Chapter', y:52},
            {name:'Book', y:6}
        ]
    }];
      
    opts = {
        chart: {
            type: 'pie',
            animation: false
        },
        title: {
            text: 'XD-Related Publications By Publication Type'
        },
        tooltip: {
            pointFormat: '{series.name}: <b>{point.y}</b>'
        },
        plotOptions: {
            pie: {
                allowPointSelect: true,
                animation: false,
                cursor: 'pointer',
                dataLabels: {
                    enabled: true,
                    color: '#000000',
                    connectorColor: '#000000',
                    format: '<b>{point.name}</b>: {point.percentage:.1f} %'
                }
            }
        },
        credits: {
            enabled: false
        },
    };
    
    var chart = new Chart('containerDistType', opts, series);
    chart.create();    
});

$(function() {
    var series = [{
        name: '# of XD related publications',
        data: [               
            {name:'2005', y:21},
            {name:'2006', y:237},
            {name:'2007', y:280},
            {name:'2008', y:289},
            {name:'2009', y:488},
            {name:'2010', y:670},
            {name:'2011', y:757},
            {name:'2012', y:1128},
            {name:'2013', y:1718},
            {name:'2014', y:1998},
            {name:'2015', y:1561},
            {name:'2016', y:872},
            {name:'2017', y:5},
        ]
    }];
    
    opts = {
        chart: {
            type: 'column',
            animation: false
        },
        title: {
            text: 'XD-Related Publications By Year Published'
        },
        tooltip: {
            pointFormat: '{series.name}: <b>{point.y}</b>'
        },
        xAxis: {
            categories: [
                '2005',
                '2006',
                '2007',
                '2008',                
                '2009',                
                '2010',                
                '2011',                
                '2012',               
                '2013',                
                '2014',               
                '2015',                
                '2016',                
                '2017',                
            ],
            labels: {
                rotation: -45,
                align: 'right',
                style: {
                    fontSize: '10px'
                }
            }
        },
        yAxis: {
            min: 0,
            title: {
                text: '# of Publications'
            }
        },
        plotOptions: {
            column: {
                pointPadding: 0.2,
                borderWidth: 0,
                animation: false
            }
        },
        credits: {
            enabled: false
        },
    };
    
    var chart = new Chart('containerDistYear', opts, series);
    chart.create();
});

$(function() {
    var chartData = fos.map(function(f){
        f['name'] = f['fos'];
        f['data'] = f['# of Pubs'];
        return f
    });
    var chart = new BarChart('fosChart', chartData, 'XD-Related Publications by Field');
    chart.draw();
});

$(function() {
    // org map
    var json = org.map(function(o){
        o['code'] = o['location_state'];
        o['value'] = o['# of Pubs'];
        return o;
    });
    var data = collapse_data(json);

    // ensure each state is represented
    var states = ['AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME', 'MI', 'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VA', 'VT', 'WA', 'WI', 'WV', 'WY'];

    var inData, state;
    for(var s = 0; s < states.length; s++){
        inData = false;
        for(var d = 0; d < data.length; d++){
            if(states[s] == data[d]['code']){
                inData = true;
                break;
            }
        }
        
        if(!inData){
            data.push({code: states[s], value: .0000001});
        }
    }
  
    Highcharts.mapChart('orgsStateMap', {
        chart: {
            animation: false
        },
        
        title: {
            text: 'XD-Related Publications by State'
        },

        mapNavigation: {
            enabled: true
        },

        colorAxis: {
            min: 1,
            type: 'logarithmic',
            minColor: '#EEEEFF',
            maxColor: '#000022',
            stops: [
                [0, '#EFEFFF'],
                [0.67, '#4444FF'],
                [1, '#000022']
            ],
        },
        
        plotOptions: {
            series: {
                animation: false
            }
        },

        series: [{
            data: data,
            mapData: Highcharts.maps['countries/us/us-all'],
            joinBy: ['postal-code', 'code'],
            dataLabels: {
                enabled: true,
                color: '#FFFFFF',
                format: '{point.code}'
            },
            name: 'Scientific Impact',
            tooltip: {
                pointFormat: '{point.name}: {point.value} publication(s)'
            }
        }]
    });
    
    // org chart
    var chartData = org.map(function(o){
        o['name'] = o['Organization'];
        o['data'] = o['# of Pubs'];
        return o;
    });
    
    var chart = new BarChart('orgsChart', chartData, 'XD-Related Publications by Organization');
    chart.draw();
});

function collapse_data(json){
	obj = {};
    ignore = ['PR', 'VI']
  
	for(var i = 0, max = json.length; i < max; i++){
        item = json[i];
        if(item['code'] && item['value'] && ignore.indexOf(item['code']) == -1){
            if(obj.hasOwnProperty(item['code'])){
                obj[item['code']] += parseInt(item['value']);
            } else {
                obj[item['code']] = parseInt(item['value']);
            }
        }
	}
    
    data = []
    for (var key in obj) {
        if (obj.hasOwnProperty(key)) {
            data.push({code: key, value: obj[key]});
        }
	}
    
    return data;
}

function BarChart(container, data, title, paginated = true){
    this.maxItems = 10;
    this.container = container;
    
    var chartData = data.map(function(d){
        if(d['name']){
            return {name: d['name'], data: parseInt(d['data'])};
        }
    }).filter(function(d){
        return typeof d != 'undefined';  
    });
    
    chartData.sort(function(a, b){
        return b['data'] - a['data'];
    });
    
    var d = [];
    var c = {};
    var numbers = [];
    for(var i = 0; i < chartData.length; i++){
        c = chartData[i];
        numbers = numbers.concat(c['data']);
        d.push([c['name'], c['data']]);
    }
    series = [{name: 'Publications', data: d}];
    
    var max = roundHighestUp(numbers);
    
    this.options = {
        chart: {
            type: 'bar',
            animation: false,
            marginLeft: 250
        },
        
        legend: {
            enabled: false
        },
        
        title: {
            text: title
        },
        
        plotOptions: {
            bar: {
                dataLabels: {
                    enabled: true
                },
                animation: false
            }
        },
        
        xAxis: {
            type: 'category'
        },
        
        yAxis: {
            title: {
                text: 'Publications'
            },
            min: 0,
            max: max
        }
    };
    
    this.options.series = JSON.parse(JSON.stringify(series)); //deep copy
    this.series = series;
    
    this.draw = function(){
        if(!paginated){
            Highcharts.chart(this.container, this.options);
        } else {
            var chartObj = this;
            this.currentPage = 1;
            this.options.series[0].data = this.series[0].data.slice(0, this.maxItems);
            
            Highcharts.chart(this.container, this.options, function(chart) {
            
                // add chart buttons for scrolling
                var left = chart.renderer.button('\u25B2', chart.plotLeft + chart.plotWidth, chart.plotHeight + chart.plotTop, function(){
                    var mi = chartObj.maxItems;
                    var cp = chartObj.currentPage;
                    if(cp > 1){
                        
                        chart.series[0].setData(chartObj.series[0].data.slice((cp - 2) * mi, (cp - 1) * mi), true, false, false);
                        chartObj.currentPage--;  
                    } 
                }).addClass('left').add();
                left.attr({'x': left.x - left.width - 5, 'y': left.y - left.height * 2});

                var right = chart.renderer.button('\u25BC', chart.plotLeft + chart.plotWidth, chart.plotHeight + chart.plotTop, function() {
                    var mi = chartObj.maxItems;
                    var cp = chartObj.currentPage;
                    if(cp < chartObj.series[0].data.length / mi){
                        chart.series[0].setData(chartObj.series[0].data.slice(cp * mi, (cp + 1) * mi), true, false, false);
                        chartObj.currentPage++;
                    } 
                }).addClass('right').add();
                right.attr({'x': right.x - right.width - 5, 'y': right.y - right.height});
                
                console.log(chart);
                
                chart.hcEvents.redraw = [function(evt){
                    newX = evt.target.plotWidth + evt.target.plotLeft;
                    left.attr({'x': newX - (left.width + 5)});
                    right.attr({'x': newX - (right.width + 5)});
                }];
                
            });
        }
    }
}

function Chart(container, options, series){
    this.container = container;
    this.options = options;
    this.series = series;    
    this.options.series = series;
    
    this.create = function(){
        Highcharts.chart(this.container, this.options);
    }
}

function roundHighestUp(numbers){
    var highest = Math.max.apply(null, numbers);
    var length = highest.toString().length
    var off = Math.pow(10, (length - 2));
    return Math.ceil(highest / off) * off;
}

/*
    Legacy
*/

function populateTable(id, title, csv, fields){
    var $div = $('#' + id);
    var $table = $('<table>');
    
    var data = CSV2JSON(csv);
    
    //table title
    if(title){
        $div.append('<h3>' + title + '</h3>');
    }
    
    //get table headers, indexes    
    $row = $('<tr>');
    var header;
    for(var i = 0, max = fields.length; i < max; i++){
        header = fields[i];
        if(fields.indexOf(header) != -1){
            $row.append('<th>' + header + '</th>');
        }
    }
    $table.append($row);
    
    //sort by # of pubs
    data.sort(function(a, b) {
        return b['# of Pubs'] - a['# of Pubs'];
    });
    
    //populate table
    var row;
    var field;
    for(var i = 0, max = data.length; i < max; i++){
        row = data[i];
        $row = $('<tr>');
        for(var j = 0, jmax = fields.length; j < jmax; j++){
            field = fields[j];
            $row.append('<td>' + row[field] + '</td>');
        }
        $table.append($row);
    }
    
    $div.append($table);
}
