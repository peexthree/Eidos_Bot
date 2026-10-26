package com.example.eidos.data

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

/**
 * 🛡️ 9. MUTEX-PROTECTED STATE STORE & OFFLINE PERSISTENCE
 * Thread-safe state container utilizing Kotlin Mutex locks to eliminate race conditions
 * on concurrent state mutations (e.g., rapid clicks, background network updates, audio events).
 */
class MutexStateStore<T>(initialState: T) {

    private val _state = MutableStateFlow(initialState)
    val state: StateFlow<T> = _state.asStateFlow()

    private val mutex = Mutex()

    suspend fun updateState(transform: (T) -> T) {
        mutex.withLock {
            val currentState = _state.value
            _state.value = transform(currentState)
        }
    }

    suspend fun getState(): T {
        return mutex.withLock {
            _state.value
        }
    }
}
