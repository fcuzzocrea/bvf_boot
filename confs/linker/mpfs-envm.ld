/*******************************************************************************
 * Copyright 2019-2023 Microchip FPGA Embedded Systems Solutions.
 *
 * SPDX-License-Identifier: MIT
 *
 * MPFS HAL Embedded Software
 *
 */
/*******************************************************************************
 * 
 * file name : mpfs_envm.ld
 * Use with Bare metal startup code.
 * Startup code runs from envm on MSS reset
 *
 * You can find details on the PolarFireSoC Memory map in the mpfs-memory-hierarchy.md
 * which can be found under the link below:
 * https://github.com/polarfire-soc/polarfire-soc-documentation
 * 
 */
 
OUTPUT_ARCH( "riscv" )
ENTRY(_start)

/*-----------------------------------------------------------------------------

-- MSS hart Reset vector

The MSS reset vector for each hart is stored securely in the MPFS.
The most common usage will be where the reset vector for each hart will be set
to the start of the envm at address 0x2022_0100, giving 128K-256B of contiguous
non-volatile storage. Normally this is where the initial boot-loader will 
reside. (Note: The first 256B page of envm is used for metadata associated with 
secure boot. When not using secure boot (mode 0,1), this area is still reserved 
by convention. It allows easier transition from non-secure to secure boot flow
during the development process.
When debugging a bare metal program that is run out of reset from envm, a linker 
script will be used whereby the program will run from LIM instead of envm.
In this case, the reset vector in the linker script is normally set to the 
start of LIM, 0x0800_0000.
This means you are not continually programming the envm each time you load a 
program and there is no limitation with break points when debugging.
See the mpfs-lim.ld example linker script when runing from LIM.

------------------------------------------------------------------------------*/

MEMORY
{
    /* Level 1 memories */
    E51_DTIM   (rwxa) : ORIGIN = 0x01000000, LENGTH =   8K
    E51_ITIM   (rwxa) : ORIGIN = 0x01800000, LENGTH =   8K
    U54_0_ITIM (rwxa) : ORIGIN = 0x01808000, LENGTH =  28K
    U54_1_ITIM (rwxa) : ORIGIN = 0x01810000, LENGTH =  28K
    U54_2_ITIM (rwxa) : ORIGIN = 0x01818000, LENGTH =  28K
    U54_3_ITIM (rwxa) : ORIGIN = 0x01820000, LENGTH =  28K

    /* Level 2 memories. 128 KiB from 2 MiB must be reserved for cache */
    LIM        (rwxa) : ORIGIN = 0x08000000, LENGTH = 512K
    SCRATCH    (rwxa) : ORIGIN = 0x0A000000, LENGTH = 512K

    /* DDR memory Layout (1GB)
     *  C : Cached
     * NC : Non-Cached
     */
    DDR_C_LOW   (rwxa) : ORIGIN = 0x80000000,   LENGTH = 768M
    DDR_NC_LOW  (rwxa) : ORIGIN = 0xC0000000,   LENGTH = 256M
    DDR_WCB_LOW (rwx) : ORIGIN  = 0xD0000000,   LENGTH = 256M
    DDR_C_HI    (rwxa) : ORIGIN = 0x1000000000, LENGTH = 1024M
    DDR_NC_HI   (rwxa) : ORIGIN = 0x1400000000, LENGTH = 0M
    DDR_WCB_HIGH (rwx) : ORIGIN = 0x1800000000, LENGTH = 0M

    /* ROM memories */
    ENVM       (rxa)  : ORIGIN = 0x20220100, LENGTH = 128K - 0x100	/* 256 B reserved for secure boot */
    QSPI_XIP   (rxa)  : ORIGIN = 0x21000000, LENGTH =  16M
}
                               
HEAP_SIZE           = 8k;   /* needs to be calculated for your application */

/* 
 * The stack size needs to be calculated for your application. It must be aligned.
 * Also Thread local storage (AKA hart local storage) is allocated for each hart 
 * as part of the stack. 
 * So the memory map will look like once apportion in startup code:              
 * stack hart0    
 * HLS hart 0                                                                    
 * stack hart1                                                                   
 * HLS hart 1                                                                    
 * etc                                                                           
 * Actual Stack size per hart = (STACK_SIZE_PER_HART - HLS_DEBUG_AREA_SIZE)                                                                 
 * note: HLS_DEBUG_AREA_SIZE is defined in mss_sw_config.h                       
 */
 
/*
 * Stack size for each hart's application.
 * These are the stack sizes that will be allocated to each hart before starting
 * each hart's application function, e51(), u54_1(), u54_2(), u54_3(), u54_4().
 */
STACK_SIZE_E51_APPLICATION = 8k;
STACK_SIZE_U54_1_APPLICATION = 0k;
STACK_SIZE_U54_2_APPLICATION = 0k;
STACK_SIZE_U54_3_APPLICATION = 0k;
STACK_SIZE_U54_4_APPLICATION = 0k;

SECTIONS
{
    PROVIDE(__l2lim_start = ORIGIN(LIM));
    PROVIDE(__l2lim_end = ORIGIN(LIM) + LENGTH(LIM));

    PROVIDE(__l2_scratchpad_load      = ORIGIN(SCRATCH));
    PROVIDE(__l2_scratchpad_start     = ORIGIN(SCRATCH));
    PROVIDE(__l2_scratchpad_vma_start = ORIGIN(SCRATCH));
    PROVIDE(__l2_scratchpad_end       = ORIGIN(SCRATCH));
    PROVIDE(__l2_scratchpad_vma_end   = ORIGIN(SCRATCH));

    PROVIDE(__text_load   = LOADADDR(.text));
    PROVIDE(__text_start  = ADDR(.text));
    PROVIDE(__text_end    = ADDR(.text) + SIZEOF(.text));

    PROVIDE(__data_load   = LOADADDR(.data));
    PROVIDE(__data_start  = ADDR(.data));
    PROVIDE(__data_end    = ADDR(.data) + SIZEOF(.data));

    PROVIDE(__srodata_load   = LOADADDR(.srodata));
    PROVIDE(__srodata_start  = ADDR(.srodata));
    PROVIDE(__srodata_end    = ADDR(.srodata) + SIZEOF(.srodata));

    PROVIDE(__sdata_load   = LOADADDR(.sdata));
    PROVIDE(__sdata_start  = ADDR(.sdata));
    PROVIDE(__sdata_end    = ADDR(.sdata) + SIZEOF(.sdata));

    PROVIDE(__bss_start  = ADDR(.bss));
    PROVIDE(__bss_end    = ADDR(.bss) + SIZEOF(.bss));

    PROVIDE(__sbss_start  = ADDR(.sbss));
    PROVIDE(__sbss_end    = ADDR(.sbss) + SIZEOF(.sbss));

    .text : ALIGN(8)
    {
        *(.text.init)
        *(.text .text.* .gnu.linkonce.t.*)
        *(.plt)
        . = ALIGN(8);
        *(.gcc_except_table)
        . = ALIGN(8);
    } > ENVM

    .rodata : {
        *(.rodata .rodata.* .gnu.linkonce.r.*)
    } > ENVM

    /* data section */
    .data : ALIGN(8)
    { 
        *(.got.plt) *(.got)
        *(.shdata)
        *(.data .data.* .gnu.linkonce.d.*)
        . = ALIGN(8);
    } > LIM AT > ENVM

    .srodata BLOCK(8) : ALIGN(8) {
        /* offset used with gp(gloabl pointer) are +/- 12 bits, so set 
           point to middle of expected sdata range */
        /* If sdata more than 4K, linker used direct addressing. 
           Perhaps we should add check/warning to linker script if sdata is > 4k */
        __global_pointer$ = . + 0x800;
        *(.srodata .srodata.* .gnu.linkonce.s.*)
        . = ALIGN(8);
    } > LIM AT > ENVM

    /* short/global data section */
    .sdata BLOCK(8) : ALIGN(8)
    {
        *(.sdata .sdata.* .gnu.linkonce.s.*)
        . = ALIGN(8);
    } > LIM AT > ENVM

    /* 
     *   The .ram_code section will contain the code that is run from RAM.
     *   We are using this code to switch the clocks including envm clock.
     *   This can not be done when running from envm
     *   This will need to be copied to ram, before any of this code is run.
     */
    .ram_code : ALIGN(8)
    {
        . = ALIGN (4);
        __sc_load = LOADADDR (.ram_code);
        __sc_start = .;
        *(.ram_codetext)        /* .ram_codetext sections (code) */
        *(.ram_codetext*)       /* .ram_codetext* sections (code)  */
        *(.ram_coderodata)      /* read-only data (constants) */
        *(.ram_coderodata*)
        . = ALIGN (4);
        __sc_end = .;
    } > E51_DTIM AT> ENVM

    /* sbss section */
    .sbss (NOLOAD) : ALIGN(8)
    {
        *(.sbss .sbss.* .gnu.linkonce.sb.*)
        *(.scommon)
        . = ALIGN(8);
    } > LIM
  
    /* sbss section */
    .bss (NOLOAD) : ALIGN(8)
    { 
        *(.shbss)
        *(.bss .bss.* .gnu.linkonce.b.*)
        *(COMMON)
        . = ALIGN(8);
    } > LIM

    /* End of uninitialized data segment */
    _end = .;
  
    .heap : ALIGN(8)
    {
        __heap_start = .;
        . += HEAP_SIZE;
        __heap_end = .;
        . = ALIGN(8);
        _heap_end = __heap_end;
    } > LIM
   
    /* must be on 4k boundary- corresponds to page size */
    .stack : ALIGN(4096)
    {
        PROVIDE(__stack_bottom_h0$ = .);
        PROVIDE(__app_stack_bottom_h0 = .);
        . += STACK_SIZE_E51_APPLICATION;
        PROVIDE(__app_stack_top_h0 = .);
        PROVIDE(__stack_top_h0$ = .);
    
        PROVIDE(__stack_bottom_h1$ = .);
        PROVIDE(__app_stack_bottom_h1$ = .);
        . += STACK_SIZE_U54_1_APPLICATION;
        PROVIDE(__app_stack_top_h1 = .);
        PROVIDE(__stack_top_h1$ = .);
    
        PROVIDE(__stack_bottom_h2$ = .);
        PROVIDE(__app_stack_bottom_h2 = .);
        . += STACK_SIZE_U54_2_APPLICATION;
        PROVIDE(__app_stack_top_h2 = .);
        PROVIDE(__stack_top_h2$ = .);
    
        PROVIDE(__stack_bottom_h3$ = .);
        PROVIDE(__app_stack_bottom_h3 = .);
        . += STACK_SIZE_U54_3_APPLICATION;
        PROVIDE(__app_stack_top_h3 = .);
        PROVIDE(__stack_top_h3$ = .);
    
        PROVIDE(__stack_bottom_h4$ = .);
        PROVIDE(__app_stack_bottom_h4 = .);
        . += STACK_SIZE_U54_4_APPLICATION;
        PROVIDE(__app_stack_top_h4 = .);
        PROVIDE(__stack_top_h4$ = .);
        
    } > LIM
}

