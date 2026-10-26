# EIDOS RPG ProGuard / R8 Optimization Rules

# KotlinX Serialization
-keepattributes *Annotation*,Signature,InnerClasses,EnclosingMethod,AnnotationDefault
-dontnote kotlinx.serialization.SerializationExtension
-keepclassmembers class * {
    @kotlinx.serialization.SerialName <fields>;
    @kotlinx.serialization.Serializable <fields>;
}
-keep @kotlinx.serialization.Serializable class * { *; }
-keepclassmembers @kotlinx.serialization.Serializable class * { *; }
-keepclassmembers class * {
    *** Companion;
}
-keepclasseswithmembers class * {
    kotlinx.serialization.KSerializer serializer(...);
}
-keepclassmembers class * extends kotlinx.serialization.internal.GeneratedSerializer {
    <init>(...);
}

# Keep Data Models & Serializable Objects Intact (No Obfuscation of DB / Serialization Fields)
-keep class com.example.eidos.data.** { *; }
-keepclassmembers class com.example.eidos.data.** { *; }

# Room Database
-keepclassmembers class androidx.room.RoomDatabase {
    public abstract <methods>;
}
-keep class * extends androidx.room.RoomDatabase { *; }
-keep @androidx.room.Entity class * { *; }
-keepclassmembers @androidx.room.Entity class * { *; }
-keep @androidx.room.Dao interface * { *; }
-keepclassmembers @androidx.room.Dao interface * { *; }
-keep @androidx.room.Database class * { *; }
-keep class androidx.room.Room
-dontwarn androidx.room.paging.**

# Retrofit / OkHttp / Ktor
-dontwarn okhttp3.**
-dontwarn okio.**
-dontwarn retrofit2.**
-keep class retrofit2.** { *; }
-keepclasseswithmembers class * {
    @retrofit2.http.* <methods>;
}

# Android Media3 / ExoPlayer
-keep class androidx.media3.exoplayer.** { *; }
-keep class androidx.media3.ui.** { *; }

# Biometrics
-keep class androidx.biometric.** { *; }

# Coil
-keep class coil.** { *; }
-dontwarn coil.**

# Jetpack Compose
-keep class androidx.compose.** { *; }
-dontwarn androidx.compose.**

# Strip Debug Logging in Release builds
-assumenosideeffects class android.util.Log {
    public static boolean isLoggable(java.lang.String, int);
    public static int v(...);
    public static int d(...);
}

