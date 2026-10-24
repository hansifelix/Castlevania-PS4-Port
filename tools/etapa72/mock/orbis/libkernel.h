// SOMENTE PARA TESTES DE HOSPEDEIRO. Não é SDK do PS4.
#pragma once
#include <pthread.h>
#include <stdint.h>
using OrbisPthread = pthread_t;
using OrbisPthreadAttr = pthread_attr_t;
extern "C" {
int scePthreadAttrInit(OrbisPthreadAttr*);
int scePthreadAttrSetstacksize(OrbisPthreadAttr*, size_t);
int scePthreadAttrDestroy(OrbisPthreadAttr*);
int scePthreadCreate(OrbisPthread*, const OrbisPthreadAttr*, void* (*)(void*), void*, const char*);
int scePthreadDetach(OrbisPthread);
void scePthreadExit(void*);
void scePthreadYield(void);
int32_t scePthreadGetthreadid(void);
OrbisPthread scePthreadSelf(void);
int scePthreadRename(OrbisPthread, const char*);
}
