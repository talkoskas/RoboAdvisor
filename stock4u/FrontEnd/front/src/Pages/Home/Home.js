import './Home.css';
import * as React from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import { useState, useContext } from 'react';
import { authContext } from '../../Context/auth.context';
import { Login } from '@mui/icons-material';
import {Dialog, DialogTitle, DialogContent, TextField, DialogActions, Button} from '@mui/material';
import { login, register } from '../../Services/Backend.service';

function Home() {
    const [open, setOpen] = useState(false);
    const [openSignUp, setOpenSignUp] = useState(false);
  
    const [auth, setAuth] = useContext(authContext);

    const handleClickOpen = () => {
        setOpen(true);
      };
    
      const handleClose = () => {
        setOpen(false);
        setOpenSignUp(false);
      };
    
      const handleSignUp = () => {
        setOpen(false);
        setOpenSignUp(true);
      };
    
      const logIn = async (userId, password) => {
        try {
          await login(userId, password);
          const credentials = { userId, password };
          localStorage.setItem("Stock4UCredentials", JSON.stringify(credentials));
          setAuth({ userId, password });
        }
        catch (e) {
          console.log('login failed', e);
        }
      }
    
      const signUp = async (userId, firstName, lastName, riskLevel, email, password) => {
        try {
          await register({ userId, email, password, firstName, lastName, riskLevel });
          setAuth({ userId, email, password, firstName, lastName, riskLevel });
        }
        catch (e) {
          console.log('Sign up failed', e);
        }
      }

    return <div className="App">
        <Typography color="#555555" variant="h2" gutterBottom> Welcome to STOCK4U! </Typography>
        <Typography component="div" variant="h3">
            Join over a million customers
        </Typography>      
        <Typography component="div" variant="h3">
            All over the world!
        </Typography>
        <div>
            <div className="Card-home">
                <Card sx={{ display: 'flex', backgroundColor: '#6482AD', color: '#fff', justifyContent: 'flex-end', alignItems: 'center', borderRadius: '0 8px 8px 0', minHeight: '120px', width: '40vw' }}>
                    <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                        <CardContent sx={{ flex: '1 0 auto' }}>
                            <Typography component="div" variant="h4">
                                Follow your profits!
                            </Typography>
                        </CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', pl: 1, pb: 1 }}>
                        </Box>
                    </Box>
                </Card>
            </div>
            <div className="Card-home" style={{display: 'flex', justifyContent: 'flex-end'}}>
                <Card sx={{ display: 'flex', backgroundColor: '#6482AD', color: '#fff', justifyContent: 'flex-start', alignItems: 'center', borderRadius: '8px 0 0 8px', minHeight: '120px', width: '40vw' }}>
                    <Box sx={{ display: 'flex', flexDirection: 'column'}}>
                        <CardContent sx={{ flex: '1 0 auto' }}>
                            <Typography component="div" variant="h4">
                                Invest without Risk!
                            </Typography>
                        </CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', pl: 1, pb: 1 }}>
                        </Box>
                    </Box>
                </Card>
            </div>

            <div className="Card-home">
                <Card sx={{ display: 'flex', backgroundColor: '#6482AD', color: '#fff', justifyContent: 'flex-end', alignItems: 'center', borderRadius: '0 8px 8px 0', minHeight: '120px', width: '40vw' }}>
                    <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                        <CardContent sx={{ flex: '1 0 auto' }}>
                            <Typography component="div" variant="h4">
                                Learn With ease!
                            </Typography>
                        </CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', pl: 1, pb: 1 }}>
                        </Box>
                    </Box>
                </Card>
            </div>
            <div className="Card-home" style={{display: 'flex', justifyContent: 'flex-end'}}>
                <Card sx={{ display: 'flex', backgroundColor: '#6482AD', color: '#fff', justifyContent: 'flex-start', alignItems: 'center', borderRadius: '8px 0 0 8px', minHeight: '120px', width: '40vw' }}>
                    <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                        <CardContent sx={{ flex: '1 0 auto' }}>
                            <Typography component="div" variant="h4">
                                Compete against your friends!
                            </Typography>
                        </CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', pl: 1, pb: 1 }}>
                        </Box>
                    </Box>
                </Card>
            </div>
            <div className="Card-home">
                <Card sx={{ display: 'flex', backgroundColor: '#6482AD', color: '#fff', justifyContent: 'flex-end', alignItems: 'center', borderRadius: '0 8px 8px 0', minHeight: '120px', width: '40vw' }}>
                    <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                        <CardContent sx={{ flex: '1 0 auto' }}>
                            <Typography component="div" variant="h4">
                                Earn achievements
                            </Typography>
                        </CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', pl: 1, pb: 1 }}>
                        </Box>
                    </Box>
                </Card>
            </div>

            <div className="Card-home" style={{display: 'flex', justifyContent: 'flex-end'}}>
                <Card sx={{ display: 'flex', backgroundColor: '#6482AD', color: '#fff', justifyContent: 'flex-start', alignItems: 'center', borderRadius: '8px 0 0 8px', minHeight: '120px', width: '40vw' }}>
                    <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                        <CardContent sx={{ flex: '1 0 auto' }}>
                            <Typography component="div" variant="h4">
                                Gain knowledge!
                            </Typography>
                        </CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', pl: 1, pb: 1 }}>
                        </Box>
                    </Box>
                </Card>
            </div>

        </div>  

        <Button
            size="large"
            edge="end"
            variant='contained'
            onClick={handleClickOpen}
            color="inherit"
            style={{margin: '30px 0'}}
        >
            <Typography variant='h4' style={{paddingRight: '6px'}}>Enter</Typography>
            <Login fontSize='large'/>
        </Button>

        <div className="Dialog">
        <Dialog
          open={open}
          onClose={handleClose}
          PaperProps={{
            component: 'form',
            onSubmit: (event) => {
              event.preventDefault();
              const formData = new FormData(event.currentTarget);
              const formJson = Object.fromEntries((formData).entries());
              logIn(formJson.userId, formJson.password);
              handleClose();
            },
          }}
        >
          <DialogTitle>Sign In</DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              required
              margin="dense"
              id="name"
              name="userId"
              label="User ID"
              type="text"
              fullWidth
              variant="standard"
            />
            <TextField
              autoFocus
              required
              margin="dense"
              id="name"
              name="password"
              label="Password"
              type="password"
              fullWidth
              variant="standard"
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={handleClose}>Cancel</Button>
            <Button type="submit">Sign In</Button>
            <Button onClick={handleSignUp}>Sign Up</Button>
          </DialogActions>
        </Dialog>

        <Dialog
          open={openSignUp}
          onClose={handleClose}
          PaperProps={{
            component: 'form',
            onSubmit: (event) => {
              event.preventDefault();
              const formData = new FormData(event.currentTarget);
              const formJson = Object.fromEntries((formData).entries());
              signUp(formJson.userId, formJson.firstName, formJson.lastName, formJson.riskLevel, formJson.email, formJson.password);
              handleClose();
            },
          }}
        >
          <DialogTitle>Sign Up</DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              required
              margin="dense"
              id="userId"
              name="userId"
              label="User ID"
              type="text"
              fullWidth
              variant="standard"
            />
            <TextField
              autoFocus
              required
              margin="dense"
              id="firstName"
              name="firstName"
              label="First Name"
              type="text"
              fullWidth
              variant="standard"
            />
            <TextField
              autoFocus
              required
              margin="dense"
              id="lastName"
              name="lastName"
              label="Last Name"
              type="text"
              fullWidth
              variant="standard"
            />
            <TextField
              autoFocus
              required
              margin="dense"
              id="riskLevel"
              name="riskLevel"
              label="Risk Level"
              type="text"
              fullWidth
              variant="standard"
            />
            <TextField
              autoFocus
              required
              margin="dense"
              id="name"
              name="email"
              label="Email Address"
              type="email"
              fullWidth
              variant="standard"
            />
            <TextField
              autoFocus
              required
              margin="dense"
              id="name"
              name="password"
              label="Password"
              type="password"
              fullWidth
              variant="standard"
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={handleClose}>Cancel</Button>
            <Button type="submit">Sign Up</Button>
          </DialogActions>
        </Dialog>
        </div>
    </div>;

}

export default Home;