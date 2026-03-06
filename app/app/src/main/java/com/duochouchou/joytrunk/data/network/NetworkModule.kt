package com.duochouchou.joytrunk.data.network

import com.duochouchou.joytrunk.BuildConfig
import com.duochouchou.joytrunk.data.api.AuthApi
import com.duochouchou.joytrunk.data.api.CliApi
import com.duochouchou.joytrunk.data.api.ImApi
import com.duochouchou.joytrunk.data.api.UserApi
import com.duochouchou.joytrunk.data.store.SettingsRepository
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

fun createOkHttpClient(settings: SettingsRepository): OkHttpClient {
    val logging = HttpLoggingInterceptor { message ->
        android.util.Log.d("JoyTrunk", message)
    }.apply {
        level = if (BuildConfig.DEBUG) HttpLoggingInterceptor.Level.BODY else HttpLoggingInterceptor.Level.NONE
    }
    return OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .addInterceptor { chain ->
            val token = settings.tokenSync
            val request = chain.request().newBuilder()
            if (!token.isNullOrEmpty()) {
                if (token.length > 50) {
                    request.addHeader("Authorization", "Bearer $token")
                } else {
                    request.addHeader("X-Owner-Id", token)
                }
            }
            chain.proceed(request.build())
        }
        .addInterceptor(logging)
        .build()
}

fun createRetrofit(baseUrl: String, client: OkHttpClient): Retrofit = Retrofit.Builder()
    .baseUrl(baseUrl.trimEnd('/') + "/")
    .client(client)
    .addConverterFactory(GsonConverterFactory.create())
    .build()

fun createAuthApi(retrofit: Retrofit): AuthApi = retrofit.create(AuthApi::class.java)
fun createUserApi(retrofit: Retrofit): UserApi = retrofit.create(UserApi::class.java)
fun createImApi(retrofit: Retrofit): ImApi = retrofit.create(ImApi::class.java)
fun createCliApi(retrofit: Retrofit): CliApi = retrofit.create(CliApi::class.java)
