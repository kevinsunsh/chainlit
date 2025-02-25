import { createTheme } from '@mui/material/styles';
import { grey, primary, white } from 'palette';

const typography = {
  fontFamily: ['Inter', 'sans-serif'].join(',')
};

const components = {
  MuiButton: {
    defaultProps: {
      disableElevation: true,
      disableRipple: true,
      sx: {
        textTransform: 'none'
      }
    }
  },
  MuiLink: {
    defaultProps: {
      fontWeight: 500
    }
  }
};

const shape = {
  borderRadius: 8
};

const success = {
  main: 'rgba(25, 195, 125, 1)',
  contrastText: white
};
const error = {
  main: 'rgba(239, 65, 70, 1)',
  contrastText: white
};

declare module '@mui/material/styles' {
  interface TypeBackground {
    paperVariant: string;
  }
}

const darkTheme = createTheme({
  typography,
  components,
  shape,
  palette: {
    mode: 'dark',
    success,
    error,
    background: {
      default: grey[850],
      paper: grey[900]
    },
    primary: {
      main: '#F80061',
      dark: primary[800],
      light: '#FFE7EB',
      contrastText: grey[100]
    },
    secondary: {
      main: '#9757D7',
      dark: '#763FB8',
      light: '#B87FE7',
      contrastText: white
    },
    divider: grey[800],
    text: {
      primary: grey[200],
      secondary: grey[400]
    }
  }
});

const lightTheme = createTheme({
  typography,
  components: components,
  shape,
  palette: {
    mode: 'light',
    success,
    error,
    background: {
      default: grey[50],
      paper: white
    },
    primary: {
      main: '#F80061',
      dark: primary[800],
      light: '#FFE7EB',
      contrastText: grey[850]
    },
    secondary: {
      main: '#9757D7',
      dark: '#763FB8',
      light: '#B87FE7',
      contrastText: white
    },
    divider: grey[200],
    text: {
      primary: grey[900],
      secondary: grey[700]
    }
  }
});

const makeTheme = (variant: 'dark' | 'light') =>
  variant === 'dark' ? darkTheme : lightTheme;

export const darkGreyButtonTheme = createTheme({
  typography,
  components,
  shape,
  palette: {
    primary: {
      main: grey[700],
      contrastText: grey[100]
    }
  }
});

export const lightGreyButtonTheme = createTheme({
  typography,
  components,
  shape,
  palette: {
    primary: {
      main: grey[200],
      contrastText: grey[700]
    }
  }
});

export default makeTheme;
