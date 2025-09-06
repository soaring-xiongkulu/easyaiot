/*
 * Copyright (C) 2022 Rockchip Electronics Co., Ltd.
 * Authors:
 *  Cerf Yu <cerf.yu@rock-chips.com>
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#ifndef _im2d_mpi_hpp_
#define _im2d_mpi_hpp_

#include "im2d_type.h"

/**
 * Create and config an rga ctx for rockit-ko
 *
 * @param flags
 *      Some configuration flags for this job
 *
 * @returns job id.
 */
IM_EXPORT_API im_ctx_id_t imbegin(uint32_t flags);

/**
 * Cancel and delete an rga ctx for rockit-ko
 *
 * @param flags
 *      Some configuration flags for this job
 *
 * @returns success or else negative error code.
 */
IM_EXPORT_API IM_STATUS imcancel(im_ctx_id_t id);


#endif /* #ifndef _im2d_mpi_hpp_ */