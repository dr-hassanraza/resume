import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Animated,
  Dimensions,
  TouchableOpacity,
  Alert,
} from 'react-native';
import {
  TextInput,
  Button,
  FAB,
  Card,
  Avatar,
  Chip,
  Portal,
  Modal,
  IconButton,
} from 'react-native-paper';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import * as DocumentPicker from 'expo-document-picker';
import * as Speech from 'expo-speech';
import io from 'socket.io-client';

interface Message {
  id: string;
  type: 'user' | 'ai' | 'system';
  content: string;
  timestamp: Date;
  metadata?: any;
}

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

const ChatScreen: React.FC = ({ navigation }: any) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [showQuickActions, setShowQuickActions] = useState(false);
  const [socket, setSocket] = useState<any>(null);
  
  const flatListRef = useRef<FlatList>(null);
  const typingAnimation = useRef(new Animated.Value(0)).current;
  const voiceAnimation = useRef(new Animated.Value(1)).current;

  // Initialize WebSocket connection
  useEffect(() => {
    const newSocket = io('ws://localhost:8000', {
      transports: ['websocket'],
    });

    newSocket.on('connect', () => {
      console.log('Connected to WebSocket');
      addMessage({
        id: Date.now().toString(),
        type: 'system',
        content: '🚀 Welcome! I\'m your AI resume assistant. Upload your resume or ask me anything!',
        timestamp: new Date(),
      });
    });

    newSocket.on('message', (data: any) => {
      setIsTyping(false);
      addMessage({
        id: Date.now().toString(),
        type: 'ai',
        content: data.message,
        timestamp: new Date(),
        metadata: data,
      });

      // Auto-speak AI responses
      if (data.message && !data.message.startsWith('🔍')) {
        Speech.speak(data.message, {
          rate: 0.9,
          pitch: 1.0,
          language: 'en-US',
        });
      }
    });

    newSocket.on('typing', (isTypingStatus: boolean) => {
      setIsTyping(isTypingStatus);
      if (isTypingStatus) {
        startTypingAnimation();
      }
    });

    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
    };
  }, []);

  const addMessage = (message: Message) => {
    setMessages(prev => [...prev, message]);
    setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated: true });
    }, 100);
  };

  const sendMessage = async () => {
    if (!inputText.trim() || !socket) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputText,
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setInputText('');
    setIsTyping(true);

    // Send to WebSocket
    socket.emit('chat', {
      type: 'chat',
      message: inputText,
      timestamp: Date.now(),
    });

    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  const startTypingAnimation = () => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(typingAnimation, {
          toValue: 1,
          duration: 500,
          useNativeDriver: true,
        }),
        Animated.timing(typingAnimation, {
          toValue: 0,
          duration: 500,
          useNativeDriver: true,
        }),
      ])
    ).start();
  };

  const handleVoiceRecord = async () => {
    if (isRecording) {
      // Stop recording
      setIsRecording(false);
      Animated.timing(voiceAnimation, {
        toValue: 1,
        duration: 200,
        useNativeDriver: true,
      }).start();
      
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      
      // Simulate voice-to-text conversion
      setTimeout(() => {
        setInputText('Optimize my resume for software engineering roles');
      }, 1000);
      
    } else {
      // Start recording
      setIsRecording(true);
      Animated.loop(
        Animated.timing(voiceAnimation, {
          toValue: 1.2,
          duration: 1000,
          useNativeDriver: true,
        })
      ).start();
      
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
    }
  };

  const handleFileUpload = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/pdf', 'application/msword'],
        copyToCacheDirectory: true,
      });

      if (!result.canceled && result.assets[0]) {
        const file = result.assets[0];
        
        addMessage({
          id: Date.now().toString(),
          type: 'user',
          content: `📄 Uploaded: ${file.name}`,
          timestamp: new Date(),
        });

        setIsTyping(true);

        // Send file info to WebSocket
        socket.emit('file_upload', {
          type: 'resume_upload',
          filename: file.name,
          size: file.size,
          uri: file.uri,
        });

        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }
    } catch (error) {
      Alert.alert('Upload Error', 'Failed to upload file. Please try again.');
    }
  };

  const quickActions = [
    { id: 'upload', title: 'Upload Resume', icon: 'document-text', action: handleFileUpload },
    { id: 'optimize', title: 'Quick Optimize', icon: 'flash', action: () => setInputText('Optimize my resume') },
    { id: 'jobs', title: 'Find Jobs', icon: 'briefcase', action: () => setInputText('Show me matching jobs') },
    { id: 'tips', title: 'Get Tips', icon: 'lightbulb', action: () => setInputText('Give me resume tips') },
  ];

  const renderMessage = ({ item, index }: { item: Message; index: number }) => {
    const isUser = item.type === 'user';
    const isSystem = item.type === 'system';

    return (
      <Animated.View
        style={[
          styles.messageContainer,
          isUser ? styles.userMessage : styles.aiMessage,
          { 
            transform: [{ 
              translateY: new Animated.Value(50).interpolate({
                inputRange: [0, 1],
                outputRange: [50, 0],
              }) 
            }] 
          }
        ]}
      >
        {!isUser && (
          <Avatar.Icon
            size={32}
            icon={isSystem ? 'cog' : 'robot'}
            style={[
              styles.avatar,
              isSystem ? styles.systemAvatar : styles.aiAvatar,
            ]}
          />
        )}

        <Card
          style={[
            styles.messageCard,
            isUser ? styles.userMessageCard : styles.aiMessageCard,
            isSystem && styles.systemMessageCard,
          ]}
        >
          <Card.Content style={styles.messageContent}>
            <Text
              style={[
                styles.messageText,
                isUser ? styles.userMessageText : styles.aiMessageText,
                isSystem && styles.systemMessageText,
              ]}
            >
              {item.content}
            </Text>
            
            <Text style={styles.timestamp}>
              {item.timestamp.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </Text>
          </Card.Content>
        </Card>

        {isUser && (
          <Avatar.Icon
            size={32}
            icon="account"
            style={styles.userAvatar}
          />
        )}
      </Animated.View>
    );
  };

  const renderTypingIndicator = () => {
    if (!isTyping) return null;

    return (
      <Animated.View
        style={[
          styles.messageContainer,
          styles.aiMessage,
          { opacity: typingAnimation }
        ]}
      >
        <Avatar.Icon
          size={32}
          icon="robot"
          style={styles.aiAvatar}
        />
        <Card style={styles.typingCard}>
          <Card.Content style={styles.typingContent}>
            <View style={styles.typingDots}>
              {[0, 1, 2].map((index) => (
                <Animated.View
                  key={index}
                  style={[
                    styles.typingDot,
                    {
                      transform: [{
                        scale: typingAnimation.interpolate({
                          inputRange: [0, 1],
                          outputRange: [0.8, 1.2],
                        })
                      }]
                    }
                  ]}
                />
              ))}
            </View>
            <Text style={styles.typingText}>AI is thinking...</Text>
          </Card.Content>
        </Card>
      </Animated.View>
    );
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={90}
    >
      <LinearGradient
        colors={['#f8fafc', '#e2e8f0']}
        style={styles.gradient}
      >
        {/* Messages List */}
        <FlatList
          ref={flatListRef}
          data={messages}
          renderItem={renderMessage}
          keyExtractor={(item) => item.id}
          style={styles.messagesList}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.messagesContent}
          ListFooterComponent={renderTypingIndicator}
        />

        {/* Input Area */}
        <View style={styles.inputContainer}>
          <Card style={styles.inputCard}>
            <View style={styles.inputRow}>
              <TextInput
                style={styles.textInput}
                placeholder="Ask me about your resume..."
                placeholderTextColor="#6b7280"
                value={inputText}
                onChangeText={setInputText}
                multiline
                maxLength={500}
                onSubmitEditing={sendMessage}
              />

              <View style={styles.inputActions}>
                <TouchableOpacity
                  onPress={handleVoiceRecord}
                  style={[
                    styles.voiceButton,
                    isRecording && styles.recordingButton,
                  ]}
                >
                  <Animated.View
                    style={{
                      transform: [{ scale: voiceAnimation }],
                    }}
                  >
                    <Ionicons
                      name={isRecording ? 'stop' : 'mic'}
                      size={24}
                      color={isRecording ? '#ef4444' : '#3b82f6'}
                    />
                  </Animated.View>
                </TouchableOpacity>

                <TouchableOpacity
                  onPress={sendMessage}
                  style={[
                    styles.sendButton,
                    !inputText.trim() && styles.disabledButton,
                  ]}
                  disabled={!inputText.trim()}
                >
                  <Ionicons name="send" size={20} color="#ffffff" />
                </TouchableOpacity>
              </View>
            </View>
          </Card>
        </View>

        {/* Quick Actions FAB */}
        <FAB
          icon="plus"
          style={styles.fab}
          onPress={() => setShowQuickActions(true)}
          color="#ffffff"
        />

        {/* Quick Actions Modal */}
        <Portal>
          <Modal
            visible={showQuickActions}
            onDismiss={() => setShowQuickActions(false)}
            contentContainerStyle={styles.quickActionsModal}
          >
            <Text style={styles.quickActionsTitle}>Quick Actions</Text>
            
            <View style={styles.quickActionsGrid}>
              {quickActions.map((action) => (
                <TouchableOpacity
                  key={action.id}
                  style={styles.quickActionItem}
                  onPress={() => {
                    action.action();
                    setShowQuickActions(false);
                  }}
                >
                  <View style={styles.quickActionIcon}>
                    <Ionicons name={action.icon as any} size={24} color="#3b82f6" />
                  </View>
                  <Text style={styles.quickActionText}>{action.title}</Text>
                </TouchableOpacity>
              ))}
            </View>

            <Button
              mode="outlined"
              onPress={() => setShowQuickActions(false)}
              style={styles.closeButton}
            >
              Close
            </Button>
          </Modal>
        </Portal>
      </LinearGradient>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },
  messagesList: {
    flex: 1,
    paddingHorizontal: 16,
  },
  messagesContent: {
    paddingTop: 16,
    paddingBottom: 20,
  },
  messageContainer: {
    flexDirection: 'row',
    marginVertical: 8,
    alignItems: 'flex-end',
  },
  userMessage: {
    justifyContent: 'flex-end',
  },
  aiMessage: {
    justifyContent: 'flex-start',
  },
  avatar: {
    marginHorizontal: 8,
  },
  aiAvatar: {
    backgroundColor: '#3b82f6',
  },
  systemAvatar: {
    backgroundColor: '#8b5cf6',
  },
  userAvatar: {
    backgroundColor: '#10b981',
  },
  messageCard: {
    maxWidth: screenWidth * 0.8,
    elevation: 2,
  },
  userMessageCard: {
    backgroundColor: '#3b82f6',
  },
  aiMessageCard: {
    backgroundColor: '#ffffff',
  },
  systemMessageCard: {
    backgroundColor: '#f3f4f6',
  },
  messageContent: {
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
  userMessageText: {
    color: '#ffffff',
  },
  aiMessageText: {
    color: '#1f2937',
  },
  systemMessageText: {
    color: '#6b7280',
  },
  timestamp: {
    fontSize: 12,
    color: '#9ca3af',
    marginTop: 4,
    textAlign: 'right',
  },
  typingCard: {
    backgroundColor: '#f3f4f6',
    maxWidth: screenWidth * 0.6,
  },
  typingContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  typingDots: {
    flexDirection: 'row',
    marginRight: 8,
  },
  typingDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#6b7280',
    marginHorizontal: 1,
  },
  typingText: {
    fontSize: 14,
    color: '#6b7280',
    fontStyle: 'italic',
  },
  inputContainer: {
    paddingHorizontal: 16,
    paddingBottom: 16,
    paddingTop: 8,
  },
  inputCard: {
    backgroundColor: '#ffffff',
    elevation: 4,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 12,
  },
  textInput: {
    flex: 1,
    fontSize: 16,
    color: '#1f2937',
    maxHeight: 100,
  },
  inputActions: {
    flexDirection: 'row',
    alignItems: 'center',
    marginLeft: 12,
  },
  voiceButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#f3f4f6',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  recordingButton: {
    backgroundColor: '#fee2e2',
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#3b82f6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  disabledButton: {
    backgroundColor: '#9ca3af',
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 100,
    backgroundColor: '#3b82f6',
  },
  quickActionsModal: {
    backgroundColor: '#ffffff',
    margin: 20,
    padding: 24,
    borderRadius: 16,
  },
  quickActionsTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1f2937',
    marginBottom: 20,
    textAlign: 'center',
  },
  quickActionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-around',
    marginBottom: 20,
  },
  quickActionItem: {
    alignItems: 'center',
    padding: 16,
    width: '45%',
    marginBottom: 16,
  },
  quickActionIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#dbeafe',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  quickActionText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1f2937',
    textAlign: 'center',
  },
  closeButton: {
    marginTop: 8,
  },
});

export default ChatScreen;