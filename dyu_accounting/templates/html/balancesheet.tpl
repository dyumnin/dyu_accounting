{%extends "base.tpl"%}
{%block title%} Balance Sheet for fy {{cfg.fy}} {%endblock%}
{%block content%}
<!--https://cleartax.in/s/balance-sheet/ -->
<h2>Balance Sheet as on 31 March {{cfg.fy+1}}</h2>

<table class="table table-bordered">
<tr><th> Particulars                                  </th> <th> Note No. </th> <th> {{cfg.fy}}-{{cfg.fy+1}}</th> <th> {{cfg.fy-1}}-{{cfg.fy}} </th> </tr>
<tr><th> I. EQUITY AND LIABILITIES                    </th> <th>          </th> <th>                                                   </th> <th>                                                    </th> </tr>
<tr><th>1) Shareholder's Funds                        </th> <th>          </th> <th>                                                   </th> <th>                                                    </th> </tr>
<tr><td>(a) Share Capital                             </td> <td>1         </td> <td>{{account.liabilities.share_capital}}              </td> <td>{{prev_account.liabilities.share_capital}}                      </td> </tr>
<tr><td>(b) Reserves and Surplus                      </td> <td>          </td> <td> {{account.liabilities.surplus}}                   </td> <td> {{account.liabilities.surplus}}                                </td> </tr>
<tr><td>(c) Money received against share warrants     </td> <td>          </td> <td>                                                   </td> <td>                                                    </td> </tr>
<tr><th>(2) Share application money pending allotment </th> <th>          </th> <th>                                                   </th> <th>                                                    </th> </tr>
<tr><th>(3) Non-Current Liabilities                   </th> <th>          </th> <th>                                                   </th> <th>                                                    </th> </tr>
<tr><td>(a) Long-term borrowings                      </td> <td>          </td> <td> {{account.liabilities.longterm_borrowing}}        </td> <td> {{prev_account.liabilities.longterm_borrowing}}                </td> </tr>
<tr><td>(b) Deferred tax liabilities (Net)            </td> <td>          </td> <td> {{account.liabilities.deferred_tax}}              </td> <td> {{prev_account.liabilities.deferred_tax}}                      </td> </tr>
<tr><td>(c) Other Long term liabilities               </td> <td>          </td> <td> {{account.liabilities.longterm_liability}}        </td> <td> {{prev_account.liabilities.longterm_liability}}                </td> </tr>
<tr><td>(d) Long term provisions                      </td> <td>          </td> <td> {{account.liabilities.longterm_provisions}}       </td> <td> {{prev_account.liabilities.longterm_provisions}}               </td> </tr>
<tr><th>(4) Current Liabilities                       </th> <th>          </th> <th>                                                   </th> <th>                                                    </th> </tr>
<tr><td>(a) Short-term borrowings                     </td> <td>          </td> <td> {{account.liabilities.shortterm_borrowing}}       </td> <td> {{prev_account.liabilities.shortterm_borrowing}}               </td> </tr>
<tr><td>(b) Trade payables                            </td> <td>          </td> <td> {{account.liabilities.trade_payable}}             </td> <td> {{prev_account.liabilities.trade_payable}}                     </td> </tr>
<tr><td>(c) Other current liabilities                 </td> <td>          </td> <td> {{account.liabilities.other_current_liabilities}} </td> <td> {{prev_account.liabilities.other_current_liabilities}}         </td> </tr>
<tr><td>(d) Short-term provisions                     </td> <td>          </td> <td> {{account.liabilities.shortterm_provisions}}      </td> <td> {{prev_account.liabilities.shortterm_provisions}}   TDS Liability, Auditor Fees          </td> </tr>
<tr><th>Total                                         </th> <th>          </th> <th> {{account.liabilities.total}}                     </th> <th> {{prev_account.liabilities.total}}                 </th> </tr>
<tr><th>II.Assets                                     </th> <th>          </th> <th>                                                   </th> <th>                                                    </th> </tr>
<tr><th>(1) Non-current assets                        </th> <th>          </th> <th> {{account.assets.non_current}}                    </th> <th> {{prev_account.assets.non_current}}                </th> </tr>
<tr><td>(a) Fixed assets                              </td> <td>          </td> <td> {{account.assets.fixed}}                          </td> <td> {{prev_account.assets.fixed}}                      </td> </tr>
<tr><td>(i) Tangible assets                           </td> <td>          </td> <td> {{account.assets.tangible}}                       </td> <td> {{prev_account.assets.tangible}}                   </td> </tr>
<tr><td>(ii) Intangible assets                        </td> <td>          </td> <td> {{account.assets.intangible}}                     </td> <td> {{prev_account.assets.intangible}}                 </td> </tr>
<tr><td>(iii) Capital work-in-progress                </td> <td>          </td> <td> {{account.assets.wip_capital}}                    </td> <td> {{prev_account.assets.wip_capital}}                </td> </tr>
<tr><td>(iv) Intangible assets under development      </td> <td>          </td> <td> {{account.assets.intangile_wip}}                  </td> <td> {{prev_account.assets.intangile_wip}}              </td> </tr>
<tr><td>(b) Non-current investments                   </td> <td>          </td> <td> {{account.assets.investments_non_current}}        </td> <td> {{prev_account.assets.investments_non_current}}    </td> </tr>
<tr><td>(c) Deferred tax assets (net)                 </td> <td>          </td> <td> {{account.assets.deferred_tax}}                   </td> <td> {{prev_account.assets.deferred_tax}}               </td> </tr>
<tr><td>(d) Long term loans and advances              </td> <td>          </td> <td> {{account.assets.longterm_loan}}                 </td> <td> {{prev_account.assets.longterm_loan}}             </td> </tr>
<tr><td>(e) Other non-current assets                  </td> <td>          </td> <td> {{account.assets.other_non_current}}              </td> <td> {{prev_account.assets.other_non_current}}          </td> </tr>
<tr><th>(2) Current assets                            </th> <th>          </th> <th>                                                   </th> <th>                                                    </th> </tr>
<tr><td>(a) Current investments                       </td> <td>          </td> <td> {{account.assets.investments}}                    </td> <td> {{prev_account.assets.investments}}                </td> </tr>
<tr><td>(b) Inventories                               </td> <td>          </td> <td> {{account.assets.inventory}}                      </td> <td> {{prev_account.assets.inventory}}                  </td> </tr>
<tr><td>(c) Trade receivables                         </td> <td>          </td> <td> {{account.assets.trade_receivables}}              </td> <td> {{prev_account.assets.trade_receivables}}          </td> </tr>
<tr><td>(d) Cash and cash equivalents                 </td> <td>          </td> <td> {{account.assets.cash}}                           </td> <td> {{prev_account.assets.cash}}                       </td> </tr>
<tr><td>(e) Short-term loans and advances             </td> <td>          </td> <td> {{account.assets.shortterm_loans}}               </td> <td> {{prev_account.assets.shortterm_loans}}           </td> </tr>
<tr><td>(f) Other current assets                      </td> <td>          </td> <td> {{account.assets.misc_current}}                   </td> <td> {{prev_account.assets.misc_current}}               </td> </tr>
<tr><th>Total                                         </th> <th>          </th> <th> {{account.assets.total}}                   </th> <th> {{prev_account.assets.total}}               </th> </tr>
</table>
{%endblock%}
