import './Investments.css';
import * as React from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import { styled } from '@mui/material/styles';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import TextField from '@mui/material/TextField';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import ToggleButton from '@mui/material/ToggleButton';
import { List, ListItem, ListItemButton, ListItemText } from '@mui/material';
import { useDebounce } from 'use-debounce';
import { TrendingDown, TrendingUp } from '@mui/icons-material';
import { Switch } from '@mui/material';
import { authContext } from '../../Context/auth.context';
import { getRealTimeStock, getInvestorStatus, enterPosition, closePosition, editStopLimit, getUserRiskLevel, getRecommendedStocks } from '../../Services/Backend.service';

const StyledTableCell = styled(TableCell)(({ theme }) => ({
    'fontSize': '15px',
    borderBottom: '1px solid #6482AD',
    color: '#fff'
}));

function createData(id, symbol, shares, type, priceOfShare, differencePrecent, differenceUSD, stopLimitPrice) {
    return { id, symbol, shares, type, priceOfShare, differencePrecent, differenceUSD, stopLimitPrice };
}


function NewPositionDialog({ open, handleClose, userRiskLevel }) {
    const [symbolText, setSymbolText] = React.useState('');
    const [symbol] = useDebounce(symbolText, 500);
    const [price, setPrice] = React.useState(undefined);
    const [amount, setAmount] = React.useState(0);
    const [symbolValid, setSymbolValid] = React.useState(false);
    const [type, setType] = React.useState("Long");
    const [limitIsActive, setLimitIsActive] = React.useState(false);
    const [stopLimitPrice, setstopLimitPrice] = React.useState(-1);
    const [recommendedStocks, setRecommendedStocks] = React.useState([]);
    const [auth] = React.useContext(authContext);

    React.useEffect(() => { getUserRecommendedStocks() }, [auth])

    async function getUserRecommendedStocks() {
        try {
            let riskLevelRsponse = await getUserRiskLevel(auth.userId);
            let recommendedStocksResponse = await getRecommendedStocks(riskLevelRsponse.data);
            setRecommendedStocks(recommendedStocksResponse.data);
        } catch (e) {
            console.error(e);
        }
    }

    async function applySymbol() {
        if (!!symbol) {
            try {
                const symbolRealTimeDataResponse = await getRealTimeStock(symbol);
                setSymbolValid(true);
                const stockCurrentPrice = symbolRealTimeDataResponse.data.c;
                setPrice(stockCurrentPrice);
            } catch (e) {
                setSymbolValid(false);
            }
        }
    }

    React.useEffect(() => { applySymbol() }, [symbol]);

    function changeSymbol(event) {
        setSymbolValid(false);
        setSymbolText(event.target.value);
    }

    function close() {
        setType("Long");
        setLimitIsActive(false);
        handleClose();
    }

    async function enterNewPosition() {
        try {
            const stockResponse = await getRealTimeStock(symbol);
            const stockCurrentPrice = stockResponse.data.c;

            const body = {
                userId: auth.userId,
                position: {
                    positionId: (new Date()).toISOString(),
                    shareSymbol: symbol,
                    shareCategory: "",
                    entryPrice: stockCurrentPrice,
                    sharesCount: amount,
                    positionType: type,
                    entryTime: new Date(),
                    stopLimitPrice: limitIsActive === false ? -1 : stopLimitPrice
                }
            };

            await enterPosition(body);
            close();
        }
        catch (e) {
            console.log('failed entering position', e);
        }

    }

    return <Dialog onClose={close} open={open}>
        <DialogTitle>New Position Parameters</DialogTitle>
        <div className='Dialog-Content'>
            <TextField label="Search Stocks" value={symbolText} onChange={changeSymbol} />

            <div>
                <Typography sx={{paddingLeft: '6px', fontSize: '12px', color: 'rgba(0, 0, 0, 0.6)'}}>Recommended Stocks:</Typography>
                <List style={{ overflowY: 'auto', maxHeight: '144px', border: '1px solid #c4c4c4', borderRadius: '6px' }}>
                    {recommendedStocks.map(stock => <ListItem key={stock.symbol} disablePadding>
                        <ListItemButton onClick={() => setSymbolText(stock.symbol)}>
                            <ListItemText primary={stock.symbol} />
                        </ListItemButton>
                    </ListItem>)}
                </List>
            </div>

            {symbolValid ? <div style={{ height: '20px' }}>Price per share: {price}$</div> : <></>}
            {!symbolValid && !!symbol ? <div style={{ height: '20px', color: '#df3a3a' }}>Symbol does not exist in our system</div> : <></>}
            <ToggleButtonGroup
                value={type}
                exclusive
                onChange={(_, value) => setType(value)}
            >
                <ToggleButton value="Long">
                    LONG
                </ToggleButton>
                <ToggleButton value="Short">
                    SHORT
                </ToggleButton>
            </ToggleButtonGroup>
            <TextField onChange={(_, value) => setAmount(_.target.value)} label="Amount" />
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", paddingTop: "20px" }}>
                <Typography style={{ fontWeight: "bold", fontSize: "16px" }}>Activate Limit</Typography>
                <Switch value={limitIsActive} onChange={() => setLimitIsActive(prev => !prev)} />
            </div>
            {limitIsActive ?
                <>
                    <Typography>
                        If you want to limit the entry price for the position, select this option
                    </Typography>
                    <TextField label="Limit" inputProps={{ type: 'number', min: 0 }} onChange={(_, value) => setstopLimitPrice(_.target.value)} />
                </>
                : null}
            <div style={{ display: "flex", justifyContent: "center", alignItems: "flex-end", paddingTop: "40px" }}>
                <Button variant='contained' onClick={enterNewPosition}>Confirm</Button>
            </div>
        </div>
    </Dialog>
}

function ConfigurestopLimitPriceDialog({ open, handleClose, positionId }) {
    const [stopLimit, setStopLimit] = React.useState(-1);
    const [auth] = React.useContext(authContext);

    function close() {
        handleClose();
    }

    async function configureStopLimit() {
        try {
            const body = {
                userId: auth.userId,
                positionId: positionId,
                stopLimitPrice: stopLimit
            };
            console.log('body', body)
            await editStopLimit(body);
            close();
        } catch (e) {
            console.log('close position failed', e);
        }
    }

    async function resetStopLimit() {
        try {
            const body = {
                userId: auth.userId,
                positionId: positionId,
                stopLimitPrice: -1
            };
            console.log('body', body)
            await editStopLimit(body);
            close();
        } catch (e) {
            console.log('close position failed', e);
        }
    }

    return <Dialog onClose={close} open={open}>
        <DialogTitle>Configure Stop Limit</DialogTitle>
        <div className='Dialog-Content'>
            <Typography style={{ fontWeight: "bold", fontSize: "16px" }}>Stop Limit Value in USD</Typography>
            <TextField onChange={(_, value) => setStopLimit(_.target.value)} label="250$" />
            <div style={{ display: "flex", justifyContent: "center", alignItems: "flex-end", paddingTop: "40px" }}>
                <Button onClick={resetStopLimit} variant='contained'>Delete current Stop Limit</Button>
                <Button style={{ marginLeft: '10px' }} onClick={configureStopLimit} variant='contained'>Confirm</Button>
            </div>
        </div>
    </Dialog>
}

function ExitPositionDialog({ open, handleClose, positionId, symbol }) {
    const [amount, setAmount] = React.useState(0);
    const [auth] = React.useContext(authContext);

    function close() {
        handleClose();
    }

    async function closeOldPosition() {
        try {
            const stockResponse = await getRealTimeStock(symbol);
            const stockCurrentPrice = stockResponse.data.c;

            const body = {
                userId: auth.userId,
                positionId: positionId,
                closePrice: stockCurrentPrice,
                closeTime: new Date(),
                sharesCount: amount ?? 0,
            };
            console.log('body', body)
            await closePosition(body);
            close();
        } catch (e) {
            console.log('close position failed', e);
        }
    }

    return <Dialog onClose={close} open={open}>
        <DialogTitle>Exit Position</DialogTitle>
        <div className='Dialog-Content'>
            <TextField onChange={(_, value) => setAmount(_.target.value)} label="Amount" />
            <div style={{ display: "flex", justifyContent: "center", alignItems: "flex-end", paddingTop: "40px" }}>
                <Button onClick={closeOldPosition} variant='contained'>Confirm</Button>
            </div>
        </div>
    </Dialog>
}

function Investments() {
    const [newPositionOpen, setNewPositionOpen] = React.useState(false);
    const [exitPositionOpen, setExitPositionOpen] = React.useState(false);
    const [configurestopLimitPrice, setConfigurestopLimitPrice] = React.useState(false);
    const [refresh, setRefresh] = React.useState(false);
    const [rows, setRows] = React.useState([]);
    const [bank, setBank] = React.useState(0);
    const [profit, setProfit] = React.useState(0);
    const [achievements, setAchievements] = React.useState(0);
    const [riskLevel, setRiskLevel] = React.useState('');
    const [auth] = React.useContext(authContext);
    const [selectedPositionId, setSelectedPositionId] = React.useState('');
    const [selectedSymbol, setSelectedSymbol] = React.useState('');
    const initialBalance = 1_000_000;

    async function getData() {
        if (!auth || !auth.userId) {
            return;
        }

        try {
            const userInvestmentStatusResponse = await getInvestorStatus(auth.userId);
            const userInvestmentStatus = userInvestmentStatusResponse.data;
            let userPositions = [];

            for (let { positionId, shareSymbol, entryPrice, sharesCount, positionType, stopLimitPrice } of userInvestmentStatus.positions) {
                try {
                    const stockResponse = await getRealTimeStock(shareSymbol);
                    const stockCurrentPrice = stockResponse.data.c;
                    const differencePrecent = ((stockCurrentPrice - entryPrice) / entryPrice) * 100;
                    const differenceUSD = stockCurrentPrice - entryPrice;

                    userPositions.push(createData(positionId, shareSymbol, sharesCount, positionType, entryPrice, differencePrecent.toFixed(2), differenceUSD.toFixed(2), stopLimitPrice));
                } catch (e) {
                    console.error(e);
                }
            }

            setRows(userPositions);
            setBank(userInvestmentStatus.accountBalance);
            setProfit((userInvestmentStatus.totalWorth - initialBalance).toFixed(2));
            setAchievements(userInvestmentStatus.achievementsCount);
            setRiskLevel(userInvestmentStatus.riskLevel)
        } catch (e) {
            console.log(e);
        }
    }

    React.useEffect(() => { getData() }, [refresh, auth]);

    function closeNewPosition() {
        setNewPositionOpen(false)
        setRefresh(prev => !prev);
    }

    function closeExitPosition() {
        setExitPositionOpen(false)
        setRefresh(prev => !prev);
    }

    function closeConfigureStopLimit() {
        setConfigurestopLimitPrice(false);
        setRefresh(prev => !prev);
    }

    function onConfigureStopLimit(show, rowId) {
        setConfigurestopLimitPrice(show);
        setSelectedPositionId(rowId);
    }

    function onClosePosition(positionId, symbol) {
        setExitPositionOpen(true);
        setSelectedPositionId(positionId);
        setSelectedSymbol(symbol);
    }

    return <div className="App">
        <Typography color="#555555" variant="h4" gutterBottom> Investments </Typography>
        <div style={{ display: 'flex', justifyContent: 'space-evenly', width: '100%' }}>
            <div className="Card">
                <Card sx={{ display: 'flex', backgroundColor: '#7FA1C3', color: '#fff', minWidth: '250px', justifyContent: 'center', borderRadius: '8px', minHeight: '120px' }}>
                    <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                        <CardContent sx={{ flex: '1 0 auto' }}>
                            <Typography component="div" color="#fff" variant="h5">
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
            <div className="Card">
                <Card sx={{ display: 'flex', backgroundColor: '#7FA1C3', color: '#fff', minWidth: '250px', justifyContent: 'center', borderRadius: '8px', minHeight: '120px' }}>
                    <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                        <CardContent sx={{ flex: '1 0 auto' }}>
                            <Typography component="div" color="#fff" variant="h5">
                                Shares Profit
                            </Typography>
                            <Typography variant="subtitle1" color="#fff" component="div">
                                {profit}$
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
                            <Typography component="div" color="#fff" variant="h5">
                                Achievements
                            </Typography>
                            <Typography variant="subtitle1" color="#fff" component="div">
                                {achievements}
                            </Typography>
                        </CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', pl: 1, pb: 1 }}>
                        </Box>
                    </Box>
                </Card>
            </div>

        </div>
        <div style={{ padding: '0 20px' }}>
            <div>
                <Typography color="#555" variant="h6" gutterBottom>My Positions</Typography>
            </div>
            <TableContainer component={Paper} sx={{ backgroundColor: '#7FA1C3', maxHeight: '60vh' }}>
                <Table stickyHeader>
                    <TableHead>
                        <TableRow>
                            <StyledTableCell sx={{ backgroundColor: '#6482AD' }} align="right">Symbol</StyledTableCell>
                            <StyledTableCell sx={{ backgroundColor: '#6482AD' }} align="right">Shares</StyledTableCell>
                            <StyledTableCell sx={{ backgroundColor: '#6482AD' }} align="right">Entry Price per Share</StyledTableCell>
                            <StyledTableCell sx={{ backgroundColor: '#6482AD' }} align="right">Type</StyledTableCell>
                            <StyledTableCell sx={{ backgroundColor: '#6482AD' }} align="right">Difference (%)</StyledTableCell>
                            <StyledTableCell sx={{ backgroundColor: '#6482AD' }} align="right">Difference ($)</StyledTableCell>
                            <StyledTableCell sx={{ backgroundColor: '#6482AD' }} align="right">Stop Limit Value</StyledTableCell>
                            <StyledTableCell sx={{ backgroundColor: '#6482AD', color: '#555' }} align="right">
                                <Button color='inherit' variant='contained' onClick={() => setNewPositionOpen(true)}>Enter New Position</Button>
                            </StyledTableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody sx={{ height: '40vh', overflowY: 'auto' }}>
                        {rows.map((row) => (
                            <TableRow key={row.id}>
                                <StyledTableCell align="right">{row.symbol}</StyledTableCell>
                                <StyledTableCell align="right">{row.shares}</StyledTableCell>
                                <StyledTableCell align="right">{row.priceOfShare}$</StyledTableCell>
                                <StyledTableCell align="right">{row.type}</StyledTableCell>
                                <StyledTableCell align="right">
                                    <div className='Difference'>
                                        {Math.abs(row.differencePrecent)}%
                                        {row.differencePrecent < 0 ?
                                            <TrendingDown style={{ color: row.type?.toLowerCase() == 'short' ? 'green' : '#df3a3a' }} /> :
                                            <TrendingUp style={{ color: row.type?.toLowerCase() == 'short' ? '#df3a3a' : 'green' }} />}
                                    </div>
                                </StyledTableCell>
                                <StyledTableCell align="right">
                                {row.differenceUSD < 0 ?
                                            <span style={{ fontWeight: 'bold', color: row.type?.toLowerCase() == 'short' ? 'green' : '#df3a3a' }}>{(row.differenceUSD * row.shares).toFixed(2)}$</span> :
                                            <span style={{ fontWeight: 'bold', color: row.type?.toLowerCase() == 'short' ? '#df3a3a' : 'green' }}>+{(row.differenceUSD * row.shares).toFixed(2)}$</span>}
                                </StyledTableCell>
                                <StyledTableCell align="right">
                                    {row.stopLimitPrice === -1 ?
                                        <>
                                            <Button size="small" variant='outlined' sx={{border: '1px solid #526b8f', color: '#526b8f'}} onClick={() => onConfigureStopLimit(true, row.id)}>Configure Stop Limit</Button>
                                        </>
                                        :
                                        <>
                                            <span style={{ marginRight: '6px' }}>{row.stopLimitPrice}$</span>
                                            <Button size="small" variant='outlined' sx={{border: '1px solid #526b8f', color: '#526b8f'}} onClick={() => onConfigureStopLimit(true, row.id)}>Reconfigure</Button>
                                        </>
                                    }
                                </StyledTableCell>
                                <StyledTableCell align="right">
                                    <Button sx={{ backgroundColor: '#526b8f' }} variant='contained' onClick={() => onClosePosition(row.id, row.symbol)}>Exit Position</Button>
                                </StyledTableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </div>
        <NewPositionDialog open={newPositionOpen} handleClose={closeNewPosition} />
        <ExitPositionDialog open={exitPositionOpen} handleClose={closeExitPosition} positionId={selectedPositionId} symbol={selectedSymbol} />
        <ConfigurestopLimitPriceDialog open={configurestopLimitPrice} handleClose={closeConfigureStopLimit} positionId={selectedPositionId} />
    </div>;
}

export default Investments;