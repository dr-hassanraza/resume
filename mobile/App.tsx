import React, { useEffect, useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Provider as PaperProvider, DefaultTheme } from 'react-native-paper';
import { Provider as ReduxProvider } from 'react-redux';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import * as Notifications from 'expo-notifications';
import { Ionicons } from '@expo/vector-icons';
import { View, Text, StyleSheet, Animated } from 'react-native';

// Screens
import SplashScreen from './src/screens/SplashScreen';
import LoginScreen from './src/screens/auth/LoginScreen';
import RegisterScreen from './src/screens/auth/RegisterScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import ChatScreen from './src/screens/ChatScreen';
import ResumeBuilderScreen from './src/screens/ResumeBuilderScreen';
import JobSearchScreen from './src/screens/JobSearchScreen';
import AnalyticsScreen from './src/screens/AnalyticsScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import CameraScreen from './src/screens/CameraScreen';
import VoiceChatScreen from './src/screens/VoiceChatScreen';

// Store and Context
import { store } from './src/store/store';
import { AuthProvider, useAuth } from './src/contexts/AuthContext';
import { ThemeProvider } from './src/contexts/ThemeContext';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

// Configure notifications
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

const theme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    primary: '#3b82f6',
    secondary: '#8b5cf6',
    accent: '#10b981',
    surface: '#ffffff',
    background: '#f8fafc',
    error: '#ef4444',
    text: '#1f2937',
    placeholder: '#6b7280',
  },
};

const MainTabNavigator = () => {
  const fadeAnim = new Animated.Value(0);

  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 300,
      useNativeDriver: true,
    }).start();
  }, []);

  return (
    <Animated.View style={[styles.container, { opacity: fadeAnim }]}>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          tabBarIcon: ({ focused, color, size }) => {
            let iconName: keyof typeof Ionicons.glyphMap;

            switch (route.name) {
              case 'Dashboard':
                iconName = focused ? 'home' : 'home-outline';
                break;
              case 'Chat':
                iconName = focused ? 'chatbubbles' : 'chatbubbles-outline';
                break;
              case 'Jobs':
                iconName = focused ? 'briefcase' : 'briefcase-outline';
                break;
              case 'Analytics':
                iconName = focused ? 'analytics' : 'analytics-outline';
                break;
              case 'Profile':
                iconName = focused ? 'person' : 'person-outline';
                break;
              default:
                iconName = 'home-outline';
            }

            return (
              <Animated.View
                style={[
                  styles.tabIcon,
                  focused && styles.focusedTabIcon,
                ]}
              >
                <Ionicons name={iconName} size={size} color={color} />
              </Animated.View>
            );
          },
          tabBarActiveTintColor: theme.colors.primary,
          tabBarInactiveTintColor: '#6b7280',
          tabBarStyle: {
            backgroundColor: theme.colors.surface,
            borderTopWidth: 1,
            borderTopColor: '#e5e7eb',
            height: 90,
            paddingBottom: 20,
            paddingTop: 10,
            shadowColor: '#000',
            shadowOffset: { width: 0, height: -2 },
            shadowOpacity: 0.1,
            shadowRadius: 8,
            elevation: 8,
          },
          tabBarLabelStyle: {
            fontSize: 12,
            fontWeight: '600',
            marginTop: 4,
          },
          headerStyle: {
            backgroundColor: theme.colors.surface,
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 2 },
            shadowOpacity: 0.1,
            shadowRadius: 4,
            elevation: 4,
          },
          headerTitleStyle: {
            fontWeight: '700',
            fontSize: 18,
            color: theme.colors.text,
          },
        })}
      >
        <Tab.Screen 
          name="Dashboard" 
          component={DashboardScreen}
          options={{
            title: 'Dashboard',
            headerShown: false,
          }}
        />
        <Tab.Screen 
          name="Chat" 
          component={ChatScreen}
          options={{
            title: 'AI Chat',
            headerRight: () => (
              <View style={styles.headerIcons}>
                <Ionicons name="mic-outline" size={24} color={theme.colors.primary} />
              </View>
            ),
          }}
        />
        <Tab.Screen 
          name="Jobs" 
          component={JobSearchScreen}
          options={{
            title: 'Job Search',
            headerRight: () => (
              <View style={styles.headerIcons}>
                <Ionicons name="filter-outline" size={24} color={theme.colors.primary} />
              </View>
            ),
          }}
        />
        <Tab.Screen 
          name="Analytics" 
          component={AnalyticsScreen}
          options={{
            title: 'Analytics',
          }}
        />
        <Tab.Screen 
          name="Profile" 
          component={ProfileScreen}
          options={{
            title: 'Profile',
          }}
        />
      </Tab.Navigator>
    </Animated.View>
  );
};

const AuthStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerShown: false,
      animation: 'slide_from_right',
    }}
  >
    <Stack.Screen name="Login" component={LoginScreen} />
    <Stack.Screen name="Register" component={RegisterScreen} />
  </Stack.Navigator>
);

const AppNavigator = () => {
  const { user, isLoading } = useAuth();
  const [showSplash, setShowSplash] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowSplash(false);
    }, 2000);

    return () => clearTimeout(timer);
  }, []);

  if (showSplash || isLoading) {
    return <SplashScreen />;
  }

  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerShown: false,
          animation: 'fade',
        }}
      >
        {user ? (
          <>
            <Stack.Screen name="Main" component={MainTabNavigator} />
            <Stack.Screen 
              name="ResumeBuilder" 
              component={ResumeBuilderScreen}
              options={{
                headerShown: true,
                title: 'Resume Builder',
                headerStyle: {
                  backgroundColor: theme.colors.primary,
                },
                headerTitleStyle: {
                  color: '#ffffff',
                  fontWeight: '700',
                },
                headerTintColor: '#ffffff',
                animation: 'slide_from_bottom',
              }}
            />
            <Stack.Screen 
              name="Camera" 
              component={CameraScreen}
              options={{
                headerShown: false,
                animation: 'slide_from_bottom',
              }}
            />
            <Stack.Screen 
              name="VoiceChat" 
              component={VoiceChatScreen}
              options={{
                headerShown: true,
                title: 'Voice Chat',
                headerStyle: {
                  backgroundColor: theme.colors.accent,
                },
                headerTitleStyle: {
                  color: '#ffffff',
                  fontWeight: '700',
                },
                headerTintColor: '#ffffff',
                animation: 'slide_from_right',
              }}
            />
            <Stack.Screen 
              name="Settings" 
              component={SettingsScreen}
              options={{
                headerShown: true,
                title: 'Settings',
                headerStyle: {
                  backgroundColor: theme.colors.surface,
                },
                headerTitleStyle: {
                  color: theme.colors.text,
                  fontWeight: '700',
                },
                headerTintColor: theme.colors.text,
                animation: 'slide_from_right',
              }}
            />
          </>
        ) : (
          <Stack.Screen name="Auth" component={AuthStack} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default function App() {
  return (
    <ReduxProvider store={store}>
      <GestureHandlerRootView style={{ flex: 1 }}>
        <SafeAreaProvider>
          <PaperProvider theme={theme}>
            <ThemeProvider>
              <AuthProvider>
                <AppNavigator />
                <StatusBar style="auto" />
              </AuthProvider>
            </ThemeProvider>
          </PaperProvider>
        </SafeAreaProvider>
      </GestureHandlerRootView>
    </ReduxProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  tabIcon: {
    padding: 4,
    borderRadius: 12,
  },
  focusedTabIcon: {
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
  },
  headerIcons: {
    marginRight: 16,
  },
});