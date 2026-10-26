package io.eidos.zerolayer.ui.components

import androidx.compose.animation.*
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import io.eidos.zerolayer.R
import io.eidos.zerolayer.ui.theme.*

enum class AuthDialogMode {
    LOGIN,
    REGISTER
}

@Composable
fun ZzzAuthDialog(
    initialMode: AuthDialogMode = AuthDialogMode.LOGIN,
    isLoading: Boolean = false,
    errorMessage: String? = null,
    onDismiss: () -> Unit,
    onLogin: (username: String, password: String) -> Unit,
    onRegister: (username: String, password: String) -> Unit
) {
    var mode by remember { mutableStateOf(initialMode) }
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var confirmPassword by remember { mutableStateOf("") }
    var passwordVisible by remember { mutableStateOf(false) }
    var confirmPasswordVisible by remember { mutableStateOf(false) }
    var localError by remember { mutableStateOf<String?>(null) }

    val haptics = LocalHapticFeedback.current
    val focusManager = LocalFocusManager.current

    // Clear local error on input or tab switch
    LaunchedEffect(mode, username, password, confirmPassword) {
        localError = null
    }

    Dialog(
        onDismissRequest = { if (!isLoading) onDismiss() },
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Black.copy(alpha = 0.85f))
                .padding(16.dp),
            contentAlignment = Alignment.Center
        ) {
            val shape = CutCornerShape(topStart = 16.dp, bottomEnd = 16.dp, topEnd = 4.dp, bottomStart = 4.dp)
            val activeBorderColor = if (mode == AuthDialogMode.LOGIN) ZzzElectricCyan else ZzzAcidYellow

            Surface(
                color = ZzzDarkSurface.copy(alpha = 0.96f),
                shape = shape,
                border = androidx.compose.foundation.BorderStroke(2.dp, activeBorderColor),
                modifier = Modifier
                    .fillMaxWidth()
                    .widthIn(max = 440.dp)
                    .clip(shape)
            ) {
                Box(modifier = Modifier.fillMaxWidth()) {
                    Image(
                        painter = painterResource(id = R.drawable.panel_card_glass),
                        contentDescription = null,
                        contentScale = ContentScale.Crop,
                        modifier = Modifier
                            .matchParentSize()
                            .alpha(0.80f)
                    )

                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .verticalScroll(rememberScrollState())
                    ) {
                        // Terminal Header Bar
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(Color(0xFF14171E).copy(alpha = 0.88f))
                                .padding(horizontal = 14.dp, vertical = 10.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Box(
                                modifier = Modifier
                                    .size(8.dp)
                                    .background(if (mode == AuthDialogMode.LOGIN) ZzzElectricCyan else ZzzAcidYellow, shape = CutCornerShape(2.dp))
                            )
                            Column {
                                Text(
                                    text = if (mode == AuthDialogMode.LOGIN) "НЕЙРО-АВТОРИЗАЦИЯ // LOGIN" else "РЕГИСТРАЦИЯ ОПЕРАТОРА // REGISTER",
                                    color = Color.White,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.ExtraBold,
                                    fontFamily = FontFamily.Monospace
                                )
                                Text(
                                    text = "EIDOS_SUPABASE_GATE v4.2 // METHOD_1",
                                    color = ZzzTextSecondary,
                                    fontSize = 9.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }

                        IconButton(
                            onClick = {
                                haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                                onDismiss()
                            },
                            enabled = !isLoading,
                            modifier = Modifier.size(28.dp)
                        ) {
                            Icon(
                                Icons.Default.Close,
                                contentDescription = "Close",
                                tint = ZzzTextSecondary,
                                modifier = Modifier.size(18.dp)
                            )
                        }
                    }

                    // Hazard Stripe Accent
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(3.dp)
                            .background(if (mode == AuthDialogMode.LOGIN) ZzzElectricCyan else ZzzAcidYellow)
                    )

                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(18.dp),
                        verticalArrangement = Arrangement.spacedBy(14.dp)
                    ) {
                        // Mode Switch Tabs
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(Color(0xFF111319), shape = CutCornerShape(6.dp))
                                .padding(3.dp),
                            horizontalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            // Login Tab
                            val isLogin = mode == AuthDialogMode.LOGIN
                            Box(
                                modifier = Modifier
                                    .weight(1f)
                                    .clip(CutCornerShape(4.dp))
                                    .background(if (isLogin) ZzzElectricCyan.copy(alpha = 0.25f) else Color.Transparent)
                                    .border(
                                        width = if (isLogin) 1.5.dp else 0.dp,
                                        color = if (isLogin) ZzzElectricCyan else Color.Transparent,
                                        shape = CutCornerShape(4.dp)
                                    )
                                    .clickable(enabled = !isLoading) {
                                        haptics.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                                        mode = AuthDialogMode.LOGIN
                                    }
                                    .padding(vertical = 8.dp),
                                contentAlignment = Alignment.Center
                            ) {
                                Text(
                                    text = "🔓 ВХОД В СЕТЬ",
                                    color = if (isLogin) ZzzElectricCyan else ZzzTextSecondary,
                                    fontWeight = FontWeight.ExtraBold,
                                    fontSize = 11.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                            }

                            // Register Tab
                            val isRegister = mode == AuthDialogMode.REGISTER
                            Box(
                                modifier = Modifier
                                    .weight(1f)
                                    .clip(CutCornerShape(4.dp))
                                    .background(if (isRegister) ZzzAcidYellow.copy(alpha = 0.25f) else Color.Transparent)
                                    .border(
                                        width = if (isRegister) 1.5.dp else 0.dp,
                                        color = if (isRegister) ZzzAcidYellow else Color.Transparent,
                                        shape = CutCornerShape(4.dp)
                                    )
                                    .clickable(enabled = !isLoading) {
                                        haptics.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                                        mode = AuthDialogMode.REGISTER
                                    }
                                    .padding(vertical = 8.dp),
                                contentAlignment = Alignment.Center
                            ) {
                                Text(
                                    text = "🛡 РЕГИСТРАЦИЯ",
                                    color = if (isRegister) ZzzAcidYellow else ZzzTextSecondary,
                                    fontWeight = FontWeight.ExtraBold,
                                    fontSize = 11.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }

                        // Info Description
                        Text(
                            text = if (mode == AuthDialogMode.LOGIN) {
                                "Введите ваш зарегистрированный позывной и пароль для загрузки персонажа из облака Supabase."
                            } else {
                                "Создайте новый профиль. Аккаунт будет мгновенно привязан к облачной базе данных без SMS и подтверждений."
                            },
                            color = ZzzTextBody,
                            fontSize = 11.5.sp,
                            lineHeight = 16.sp
                        )

                        // Error Banner (if any)
                        val activeError = localError ?: errorMessage
                        if (!activeError.isNullOrBlank()) {
                            Surface(
                                color = ZzzHotMagenta.copy(alpha = 0.15f),
                                border = androidx.compose.foundation.BorderStroke(1.dp, ZzzHotMagenta),
                                shape = CutCornerShape(4.dp),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Row(
                                    modifier = Modifier.padding(10.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    Text("⚠", fontSize = 16.sp)
                                    Text(
                                        text = activeError,
                                        color = Color.White,
                                        fontSize = 11.sp,
                                        fontWeight = FontWeight.Bold,
                                        lineHeight = 15.sp
                                    )
                                }
                            }
                        }

                        // Input 1: Callsign / Username
                        OutlinedTextField(
                            value = username,
                            onValueChange = { username = it },
                            label = { Text("Позывной (Логин)", fontSize = 12.sp) },
                            placeholder = { Text("например: Cypher_01", color = Color.Gray, fontSize = 12.sp) },
                            singleLine = true,
                            enabled = !isLoading,
                            leadingIcon = {
                                Icon(Icons.Default.Person, contentDescription = null, tint = if (mode == AuthDialogMode.LOGIN) ZzzElectricCyan else ZzzAcidYellow)
                            },
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedTextColor = Color.White,
                                unfocusedTextColor = Color.White,
                                focusedBorderColor = if (mode == AuthDialogMode.LOGIN) ZzzElectricCyan else ZzzAcidYellow,
                                unfocusedBorderColor = Color.DarkGray,
                                focusedLabelColor = if (mode == AuthDialogMode.LOGIN) ZzzElectricCyan else ZzzAcidYellow,
                                unfocusedLabelColor = ZzzTextSecondary,
                                cursorColor = ZzzElectricCyan
                            ),
                            keyboardOptions = KeyboardOptions(imeAction = ImeAction.Next),
                            shape = CutCornerShape(4.dp),
                            modifier = Modifier.fillMaxWidth()
                        )

                        // Input 2: Password
                        OutlinedTextField(
                            value = password,
                            onValueChange = { password = it },
                            label = { Text("Ключ доступа (Пароль)", fontSize = 12.sp) },
                            placeholder = { Text("минимум 6 знаков", color = Color.Gray, fontSize = 12.sp) },
                            singleLine = true,
                            enabled = !isLoading,
                            visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                            leadingIcon = {
                                Icon(Icons.Default.Lock, contentDescription = null, tint = if (mode == AuthDialogMode.LOGIN) ZzzElectricCyan else ZzzAcidYellow)
                            },
                            trailingIcon = {
                                IconButton(onClick = { passwordVisible = !passwordVisible }) {
                                    Text(
                                        text = if (passwordVisible) "🙈" else "👁",
                                        fontSize = 16.sp
                                    )
                                }
                            },
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedTextColor = Color.White,
                                unfocusedTextColor = Color.White,
                                focusedBorderColor = if (mode == AuthDialogMode.LOGIN) ZzzElectricCyan else ZzzAcidYellow,
                                unfocusedBorderColor = Color.DarkGray,
                                focusedLabelColor = if (mode == AuthDialogMode.LOGIN) ZzzElectricCyan else ZzzAcidYellow,
                                unfocusedLabelColor = ZzzTextSecondary,
                                cursorColor = ZzzElectricCyan
                            ),
                            keyboardOptions = KeyboardOptions(
                                keyboardType = KeyboardType.Password,
                                imeAction = if (mode == AuthDialogMode.REGISTER) ImeAction.Next else ImeAction.Done
                            ),
                            keyboardActions = KeyboardActions(
                                onDone = {
                                    focusManager.clearFocus()
                                    if (mode == AuthDialogMode.LOGIN && username.isNotBlank() && password.isNotBlank()) {
                                        onLogin(username, password)
                                    }
                                }
                            ),
                            shape = CutCornerShape(4.dp),
                            modifier = Modifier.fillMaxWidth()
                        )

                        // Input 3: Confirm Password (Register mode only)
                        if (mode == AuthDialogMode.REGISTER) {
                            OutlinedTextField(
                                value = confirmPassword,
                                onValueChange = { confirmPassword = it },
                                label = { Text("Подтвердите пароль", fontSize = 12.sp) },
                                singleLine = true,
                                enabled = !isLoading,
                                visualTransformation = if (confirmPasswordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                                leadingIcon = {
                                    Icon(Icons.Default.Lock, contentDescription = null, tint = ZzzAcidYellow)
                                },
                                trailingIcon = {
                                    IconButton(onClick = { confirmPasswordVisible = !confirmPasswordVisible }) {
                                        Text(
                                            text = if (confirmPasswordVisible) "🙈" else "👁",
                                            fontSize = 16.sp
                                        )
                                    }
                                },
                                colors = OutlinedTextFieldDefaults.colors(
                                    focusedTextColor = Color.White,
                                    unfocusedTextColor = Color.White,
                                    focusedBorderColor = ZzzAcidYellow,
                                    unfocusedBorderColor = Color.DarkGray,
                                    focusedLabelColor = ZzzAcidYellow,
                                    unfocusedLabelColor = ZzzTextSecondary,
                                    cursorColor = ZzzAcidYellow
                                ),
                                keyboardOptions = KeyboardOptions(
                                    keyboardType = KeyboardType.Password,
                                    imeAction = ImeAction.Done
                                ),
                                keyboardActions = KeyboardActions(
                                    onDone = { focusManager.clearFocus() }
                                ),
                                shape = CutCornerShape(4.dp),
                                modifier = Modifier.fillMaxWidth()
                            )
                        }

                        Spacer(modifier = Modifier.height(4.dp))

                        // Submit Button
                        if (isLoading) {
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(46.dp)
                                    .background(Color(0xFF1B1E28), shape = CutCornerShape(6.dp))
                                    .border(1.dp, activeBorderColor.copy(alpha = 0.5f), shape = CutCornerShape(6.dp)),
                                contentAlignment = Alignment.Center
                            ) {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                                ) {
                                    CircularProgressIndicator(
                                        modifier = Modifier.size(18.dp),
                                        color = activeBorderColor,
                                        strokeWidth = 2.dp
                                    )
                                    Text(
                                        text = "УСТАНОВКА НЕЙРО-СВЯЗИ С SUPABASE...",
                                        color = Color.White,
                                        fontSize = 10.5.sp,
                                        fontWeight = FontWeight.ExtraBold,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }
                            }
                        } else {
                            ZzzMainButton(
                                text = if (mode == AuthDialogMode.LOGIN) "ПОДКЛЮЧИТЬСЯ К СЕТИ // LOGIN" else "СОЗДАТЬ НЕЙРО-ПРОФИЛЬ // REGISTER",
                                onClick = {
                                    focusManager.clearFocus()
                                    haptics.performHapticFeedback(HapticFeedbackType.LongPress)

                                    val cleanUser = username.trim()
                                    if (cleanUser.length < 3) {
                                        localError = "Позывной должен содержать от 3 символов."
                                        return@ZzzMainButton
                                    }
                                    if (password.length < 6) {
                                        localError = "Пароль должен содержать минимум 6 знаков."
                                        return@ZzzMainButton
                                    }
                                    if (mode == AuthDialogMode.REGISTER && password != confirmPassword) {
                                        localError = "Введенные пароли не совпадают!"
                                        return@ZzzMainButton
                                    }

                                    if (mode == AuthDialogMode.LOGIN) {
                                        onLogin(cleanUser, password)
                                    } else {
                                        onRegister(cleanUser, password)
                                    }
                                },
                                primaryColor = if (mode == AuthDialogMode.LOGIN) ZzzElectricCyan else ZzzAcidYellow,
                                borderColor = if (mode == AuthDialogMode.LOGIN) ZzzAcidYellow else ZzzElectricCyan,
                                modifier = Modifier.fillMaxWidth()
                            )
                        }

                        // Offline Guest Notice
                        Text(
                            text = "💡 Примечание: Прогресс всегда сохраняется локально в защищенной базе Room DB. Вход в Supabase позволяет переносить прогресс между устройствами и участвовать в PvP-рейтингах.",
                            color = ZzzTextSecondary,
                            fontSize = 9.5.sp,
                            lineHeight = 13.5.sp,
                            textAlign = TextAlign.Center,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                }
            }
        }
    }
}
}
