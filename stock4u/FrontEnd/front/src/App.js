import { BrowserRouter} from "react-router-dom";
import AuthProvider from './Context/auth.context';
import { styled } from '@mui/material';
import Panels from './Panels';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Container>
          <Panels/>
        </Container>
      </BrowserRouter>
    </AuthProvider>
  );
}

const Container = styled('div')`
  text-align: center;
  height: 100vh;
`

export default App;
