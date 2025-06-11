import { createContext, useState, useEffect } from 'react';

export const authContext = createContext();

const AuthProvider = ({ children }) => {
    const [auth, setAuth] = useState({});

    useEffect(() => {
        const credentials = JSON.parse(localStorage.getItem('Stock4UCredentials'));
        if (credentials) {
            setAuth(credentials);
        }
    }, []);

    return (
        <authContext.Provider value={[auth, setAuth]}>
            {children}
        </authContext.Provider>
    );
};

export default AuthProvider;
