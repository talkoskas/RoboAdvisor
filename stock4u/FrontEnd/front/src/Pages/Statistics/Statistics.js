import './Statistics.css';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Button from '@mui/material/Button';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import { useState, useEffect, useContext } from 'react';
import { authContext } from '../../Context/auth.context';
import { AgChartsReact } from 'ag-charts-react';
import { getInvestorStatus, getStockHistory, getRealTimeStock } from '../../Services/Backend.service';
import { FormControl, InputLabel, MenuItem, Select } from '@mui/material';

function Statistics() {
    const [bank, setBank] = useState(0);
    const [risk, setRisk] = useState('');
    const [positions, setPositions] = useState([]);
    const [auth] = useContext(authContext);
    const [chartOptions, setChartOptions] = useState({});
    const [selectedShare, setSelectedShare] = useState('SPY');
    const [donutOptions, setDonutOptions] = useState({});
    const [daysBack, setDaysBack] = useState(7);
    const [options, setOptions] = useState({});
    const establishedPositions = [];

    async function handleOnButtonClick(shareSymbol, newDaysBack) {
        setSelectedShare(shareSymbol)
        try {
            const historyPrice = (await getStockHistory(shareSymbol, newDaysBack ?? daysBack)).data;
            const newLineDate = Object.keys(historyPrice).map(key => ({ date: key, shareProfit: historyPrice[key].closePrice }));

            const newOptions = {
                title: {
                    text: `Share ${shareSymbol} Over Time`,
                },
                data: newLineDate,
                series: [
                    {
                        type: "line",
                        xKey: "date",
                        yKey: "shareProfit",
                        yName: "profit"
                    }
                ],
            }

            setOptions(newOptions);
        } catch (e) {
            console.log('failed getting history', e);
        }
    }

    useEffect(() => {
        if (!positions.length) {
            getPositions();
        }
    }, [auth]);

    async function getPositions(newDaysBack) {
        if (!auth || !auth.userId) {
            return;
        }

        try {
            const userInvestmentStatusResponse = await getInvestorStatus(auth.userId);
            const userInvestmentStatus = userInvestmentStatusResponse.data;

            const newRows = [];
            userInvestmentStatus.positions.forEach(async position => {

                if (establishedPositions.includes(position.shareSymbol)) {
                    return;
                }

                establishedPositions.push(position.shareSymbol)
                try {
                    const realTimeResponse = await getRealTimeStock(position.shareSymbol);
                    const realTimeValue = realTimeResponse.data;

                    const newLineDate = [];

                    const historyResponse = await getStockHistory(position.shareSymbol, newDaysBack ?? daysBack);
                    const historyPrice = historyResponse.data;

                    Object.keys(historyPrice).forEach(key => {
                        newLineDate.push({ date: key, shareProfit: historyPrice[key].closePrice });
                    });

                    const newOptions = {
                        title: {
                            text: `Share ${position.shareSymbol} Over Time`,
                        },
                        data: newLineDate,
                        series: [
                            {
                                type: "line",
                                xKey: "date",
                                yKey: "shareProfit",
                                yName: "profit"
                            }
                        ],
                    };

                    const newDonutOptions = {
                        data: newLineDate,
                        title: {
                            text: ` ${auth.userId} - Profits Per Day`,
                        },
                        series: [
                            {
                                type: "donut",
                                calloutLabelKey: "date",
                                angleKey: "shareProfit",
                                innerRadiusRatio: 0.7,
                            },
                        ],
                    };

                    setOptions(newOptions);
                    setDonutOptions(newDonutOptions);

                    newRows.push({
                        shareKey: position.shareSymbol,
                        sharesCount: realTimeValue.c - position.entryPrice
                    });

                    setChartOptions({
                        title: {
                            text: "Profits per share",
                        }, data: newRows, series: [{ type: 'bar', xKey: 'shareKey', yKey: 'sharesCount' }]
                    });

                    const userInvestmentStatusResponse = await getInvestorStatus(auth.userId);
                    const userInvestmentStatus = userInvestmentStatusResponse.data;

                    setBank(userInvestmentStatus.accountBalance);
                    setRisk(userInvestmentStatus.riskLevel);
                } catch (e) {
                    console.error(e);
                }
            });

              const filteredPositions = []
              const newPosition = userInvestmentStatus.positions.filter(position => {
                  if (!filteredPositions.includes(position.shareSymbol)) {
                    filteredPositions.push(position.shareSymbol);    
                    return true;
                } 

                return false;
              })
              
            setPositions(newPosition);
        } catch (e) {
            console.error(e);
        }
    };

    async function onDaysBackChange(newDaysBack) {
        setDaysBack(newDaysBack);
        handleOnButtonClick(selectedShare, newDaysBack);
        await getPositions(newDaysBack);
    }

    return (
        <div className="App">
            <Typography color="#555" variant="h4" gutterBottom> Statistics </Typography>
            <div style={{ display: 'flex', justifyContent: 'space-evenly', width: '100%' }}>
                <div className="Card">
                    <Card sx={{ display: 'flex', backgroundColor: '#7FA1C3', color: '#fff', minWidth: '250px', justifyContent: 'center', borderRadius: '8px', minHeight: '120px' }}>
                        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                            <CardContent sx={{ flex: '1 0 auto' }}>
                                <Typography component="div" variant="h5">
                                    Begginner Investor
                                </Typography>
                                <Typography variant="subtitle1" color="#fff" component="div">
                                    {risk} Risk Behavior
                                </Typography>
                            </CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', pl: 1, pb: 1 }}>
                            </Box>
                        </Box>
                    </Card>
                </div>

                <div className="Card">
                    <Card sx={{ display: 'flex', backgroundColor: '#7FA1C3', color: '#fff', minWidth: '250px', justifyContent: 'center', borderRadius: '8px', minHeight: '120px' }}>
                        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                            <CardContent sx={{ flex: '1 0 auto' }}>
                                <Typography component="div" variant="h5">
                                    Budget
                                </Typography>
                                <Typography variant="subtitle1" color="#fff" component="div">
                                    {bank}$
                                </Typography>
                            </CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', pl: 1, pb: 1 }}>
                            </Box>
                        </Box>
                    </Card>
                </div>
            </div>
            <div>
                <FormControl sx={{ m: 1, minWidth: 300 }}>
                    <InputLabel id="demo-simple-select-autowidth-label">Days Back</InputLabel>
                    <Select
                        labelId="demo-simple-select-autowidth-label"
                        id="demo-simple-select-autowidth"
                        value={daysBack}
                        onChange={(e) => onDaysBackChange(+e.target.value)}
                        autoWidth
                        label="Days Back"
                    >
                        <MenuItem value={1}>Day</MenuItem>
                        <MenuItem value={7}>Week</MenuItem>
                        <MenuItem value={30}>Month</MenuItem>
                    </Select>
                </FormControl>
            </div>


            <div className="graphs">
                    {positions.map(position => <Button key={position.positionId} onClick={async () => {
                        try {
                            await handleOnButtonClick(position.shareSymbol, null)
                        } catch (e) {
                            console.log(e);
                        }
                    }}>{position.shareSymbol}</Button>)}
                <div className="charts-sections">
                    <AgChartsReact options={options} />
                </div>
                <div className="charts-sections">
                    <AgChartsReact options={chartOptions} />
                </div>
                <div className="charts-sections">
                    <AgChartsReact options={donutOptions} />
                </div>
            </div>
        </div>
    );

}

export default Statistics;