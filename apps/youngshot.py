import math
import numpy as np
import pandas as pd
import datetime
import os
import json
import os.path
import matplotlib.pyplot as plt
import plotly.express as px
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import collections
import cufflinks as cf
from app import app
import logging

# files name
feedAttrFileName = '年轻人冷启投放标签.xlsx'
cousumeDetailFileName = '热点视频消费数据.csv'

# get data directory
dataDir = os.path.join(os.getcwd(), 'data')

# load feed attr file
feedAttrFile = os.path.join(dataDir, feedAttrFileName)
feedAttrDf = pd.read_excel(feedAttrFile,
                           header=0,
                           names=[
                               '填写人', '微视账号昵称', '视频id',
                               '玩法分类', '玩法名称', '视频时长', '使用素材数量', '视频所在品类', '使用素材类型',
                               '是否使用贴纸', '是否使用特效', '素材使用主题', '预期评级',
                               '是否蹭热点', '是否带话题', '是否绑定挑战赛', '是否文案引导'],
                           dtype={
                               '填写人': str, '微视账号昵称': str, '视频id': str,
                               '玩法分类': str, '视频时长': float, '使用素材数量': str, '视频所在品类': str, '使用素材类型': str,
                               '是否使用贴纸': str, '是否使用特效': str, '素材使用主题': str,
                               '是否蹭热点': str, '是否带话题': str, '是否绑定挑战赛': str, '是否文案引导': str
                           })
feedAttrDf['视频时长区间'] = pd.cut(feedAttrDf['视频时长'], [0, 8, 12, 16, 20, 100], labels=[
    "(0,8]", "(8,12]", "(12,16]", "(16,20]", "20s以上"])

# load cousume detail file
consumeDetailFile = os.path.join(dataDir, cousumeDetailFileName)
consumeDetailDf = pd.read_csv(consumeDetailFile,
                              header=0,
                              names=[
                                  '视频id', '性别', '城市等级', '历史发布频次', '大盘播放VV', '年轻人播放VV', '年轻人播放VV占比',
                                  '大盘完播率', '年轻人完播率', '大盘互动率', '年轻人互动率',
                                  '大盘单vv时长', '年轻人单vv时长', '大盘播放完成度', '年轻人播放完成度',
                                  '大盘3s快滑率', '年轻人3s快滑率', '大盘5s快滑率', '年轻人5s快滑率'])
consumeDetailDf = consumeDetailDf.fillna(0)
consumeDetailDf = consumeDetailDf.replace(np.nan, 0)
consumeDetailDf = consumeDetailDf.astype({
    '视频id': str, '性别': str, '城市等级': str, '历史发布频次': str,
    '大盘播放VV': pd.Int64Dtype(), '年轻人播放VV': pd.Int64Dtype(), '年轻人播放VV占比': float,
    '大盘完播率': float, '年轻人完播率': float, '大盘互动率': float, '年轻人互动率': float,
    '大盘单vv时长': float, '年轻人单vv时长': float, '大盘播放完成度': float, '年轻人播放完成度': float,
    '大盘3s快滑率': float, '年轻人3s快滑率': float, '大盘5s快滑率': float, '年轻人5s快滑率': float})
consumeDetailDf['大盘3s快滑率'] = round(consumeDetailDf['大盘3s快滑率']/100, 2)
consumeDetailDf['大盘5s快滑率'] = round(consumeDetailDf['大盘5s快滑率']/100, 2)

# group cousume detail data to per_feed level
consumeStatDf = consumeDetailDf.groupby('视频id').agg({
    '大盘播放VV': 'sum', '年轻人播放VV': 'sum', '年轻人播放VV占比': ['mean', 'median'],
    '大盘完播率': ['mean', 'median'], '年轻人完播率': ['mean', 'median'], '大盘互动率': ['mean', 'median'], '年轻人互动率': ['mean', 'median'],
    '大盘单vv时长': ['mean', 'median'], '年轻人单vv时长': ['mean', 'median'], '大盘播放完成度': ['mean', 'median'], '年轻人播放完成度': ['mean', 'median'],
    '大盘3s快滑率': ['mean', 'median'], '年轻人3s快滑率': ['mean', 'median'], '大盘5s快滑率': ['mean', 'median'], '年轻人5s快滑率': ['mean', 'median']
})
consumeStatDf.columns = ['_'.join(col) for col in consumeStatDf.columns]
consumeStatDf.reset_index(inplace=True)

# merge feed attr info with consume detial
feedAttrConsumeDetailDf = pd.merge(
    feedAttrDf, consumeDetailDf, on='视频id', how='left')
feedAttrConsumeDetailDf.sort_values(by=['视频id', '大盘播放VV'], ascending=[
                                    True, False], inplace=True)
# merge feed attr info with consume stat
feedAttrConsumeStatDf = pd.merge(
    feedAttrDf, consumeStatDf, on='视频id', how='left')
feedAttrConsumeStatDf.sort_values(
    by=['大盘播放VV_sum'], ascending=False, inplace=True)


# Intermediate dataframe object for filtering
def getSubDf(mode_name='all', dimension='all'):
    if (mode_name == 'all' or dimension == 'all'):
        return feedAttrConsumeStatDf

    else:
        # mode_feedAttrConsumeStatDf = feedAttrConsumeStatDf
        mode_feedAttrConsumeStatDf = feedAttrConsumeStatDf.query(
            "玩法名称.str.contains(@mode_name)")
        dimension_mode_feedAttrConsumeStatDf = mode_feedAttrConsumeStatDf.groupby(dimension).agg({
            '视频id': 'count',
            '大盘播放VV_sum': 'sum', '年轻人播放VV_sum': 'sum',
            '大盘完播率_mean': 'mean', '大盘完播率_median': 'median',
            '年轻人完播率_mean': 'mean', '年轻人完播率_median': 'median',
            '大盘互动率_mean': 'mean', '大盘互动率_median': 'median',
            '年轻人互动率_mean': 'mean', '年轻人互动率_median': 'median',
            '大盘单vv时长_mean': 'mean', '大盘单vv时长_median': 'median',
            '年轻人单vv时长_mean': 'mean', '年轻人单vv时长_median': 'median',
            '大盘播放完成度_mean': 'mean', '大盘播放完成度_median': 'median',
            '年轻人播放完成度_mean': 'mean', '年轻人播放完成度_median': 'median',
            '大盘3s快滑率_mean': 'mean', '大盘3s快滑率_median': 'median',
            '年轻人3s快滑率_mean': 'mean', '年轻人3s快滑率_median': 'median',
            '大盘5s快滑率_mean': 'mean', '大盘5s快滑率_median': 'median',
            '年轻人5s快滑率_mean': 'mean', '年轻人5s快滑率_median': 'median'
        }).reset_index()

        dimension_mode_feedAttrConsumeStatDf.rename(
            columns={'视频id': '视频数量'}, inplace=True)
        dimension_mode_feedAttrConsumeStatDf['大盘条均播放VV'] = dimension_mode_feedAttrConsumeStatDf['大盘播放VV_sum'] / \
            dimension_mode_feedAttrConsumeStatDf['视频数量']
        dimension_mode_feedAttrConsumeStatDf['年轻人条均播放VV'] = dimension_mode_feedAttrConsumeStatDf['年轻人播放VV_sum'] / \
            dimension_mode_feedAttrConsumeStatDf['视频数量']

        dimension_mode_feedAttrConsumeStatDfTidy = pd.melt(
            dimension_mode_feedAttrConsumeStatDf, id_vars=dimension)
        # 统计方式
        dimension_mode_feedAttrConsumeStatDfTidy['统计方式'] = pd.np.where(dimension_mode_feedAttrConsumeStatDfTidy.variable.str.contains('mean|条均'), '平均',
                                                                       pd.np.where(dimension_mode_feedAttrConsumeStatDfTidy.variable.str.contains('median'), '中位数',
                                                                                   pd.np.where(dimension_mode_feedAttrConsumeStatDfTidy.variable.str.contains('sum'), '累加', 'other')))
        # 人群
        dimension_mode_feedAttrConsumeStatDfTidy['人群'] = pd.np.where(dimension_mode_feedAttrConsumeStatDfTidy.variable.str.contains('大盘'), '大盘',
                                                                     pd.np.where(dimension_mode_feedAttrConsumeStatDfTidy.variable.str.contains('年轻人'), '年轻人', 'other'))

        # 指标
        dimension_mode_feedAttrConsumeStatDfTidy['指标'] = pd.np.where(dimension_mode_feedAttrConsumeStatDfTidy.variable.str.contains('完播率'), '完播率',
                                                                     pd.np.where(dimension_mode_feedAttrConsumeStatDfTidy.variable.str.contains('互动率'), '互动率',
                                                                                 pd.np.where(dimension_mode_feedAttrConsumeStatDfTidy.variable.str.contains('单vv时长'), '单vv时长',
                                                                                             pd.np.where(dimension_mode_feedAttrConsumeStatDfTidy.variable.str.contains('播放完成度'), '播放完成度',
                                                                                                         pd.np.where(dimension_mode_feedAttrConsumeStatDfTidy.variable.str.contains('3s快滑率'), '3s快滑率',
                                                                                                                     pd.np.where(dimension_mode_feedAttrConsumeStatDfTidy.variable.str.contains('5s快滑率'), '5s快滑率',
                                                                                                                                 pd.np.where(dimension_mode_feedAttrConsumeStatDfTidy.variable.str.contains('条均播放VV'), '条均播放VV',
                                                                                                                                             pd.np.where(dimension_mode_feedAttrConsumeStatDfTidy.variable.str.contains('播放VV'), '播放VV', 'other'))))))))

        dimension_mode_feedAttrConsumeStatDfTidy.fillna(
            value={'value': 0}, inplace=True)
        return dimension_mode_feedAttrConsumeStatDfTidy


# Intermediate dataframe object for filtering, by duration to support scatter chart
def getSubDf_byduration(mode_name='all', dimension='all'):
    if (mode_name == 'all' or dimension == 'all'):
        return feedAttrConsumeStatDf

    else:
        mode_feedAttrConsumeStatDf = feedAttrConsumeStatDf.query(
            "玩法名称.str.contains(@mode_name)")[{dimension, '视频id', '视频时长', '大盘播放VV_sum', '年轻人播放VV_sum'}]
        mode_feedAttrConsumeStatDf.rename(
            columns={'大盘播放VV_sum': '大盘播放VV', '年轻人播放VV_sum': '年轻人播放VV'}, inplace=True)

        mode_feedAttrConsumeStatDfTidy = pd.melt(
            mode_feedAttrConsumeStatDf, id_vars=[dimension, '视频id', '视频时长'])
        # 人群
        mode_feedAttrConsumeStatDfTidy['人群'] = pd.np.where(mode_feedAttrConsumeStatDfTidy.variable.str.contains('大盘'), '大盘',
                                                           pd.np.where(mode_feedAttrConsumeStatDfTidy.variable.str.contains('年轻人'), '年轻人', 'other'))

        mode_feedAttrConsumeStatDfTidy.fillna(value={'value': 0}, inplace=True)
        return mode_feedAttrConsumeStatDfTidy


# The application layout structure
layout = html.Div([
    # empty Div to trigger javascript file for graph resizing
    html.Div(id="output-clientside"),

    # 1st block - selection & statistic
    html.Div(
        [
            # selection
            html.Div(
                [   # dimension selection
                    html.Div(
                        [
                            html.H6('玩法'),
                            dcc.Dropdown(
                                id='mode_dropdown',
                                options=[
                                    {'label': '冬至快乐', 'value': '冬至快乐'},
                                    {'label': '茫', 'value': '茫'},
                                    {'label': '圣诞朋友圈', 'value': '圣诞朋友圈'}
                                ],
                                value='冬至快乐'
                            ),

                            html.H6('拆解维度'),
                            dcc.Dropdown(
                                id='dimension_dropdown',
                                options=[
                                    {'label': '视频时长区间', 'value': '视频时长区间'},
                                    {'label': '素材使用主题', 'value': '素材使用主题'},
                                    {'label': '视频所在品类', 'value': '视频所在品类'},
                                    {'label': '使用素材数量', 'value': '使用素材数量'},
                                    {'label': '使用素材类型', 'value': '使用素材类型'},
                                    {'label': '是否使用贴纸', 'value': '是否使用贴纸'},
                                    {'label': '是否使用特效', 'value': '是否使用特效'},
                                    {'label': '预期评级', 'value': '预期评级'},
                                    {'label': '是否蹭热点', 'value': '是否蹭热点'},
                                    {'label': '是否带话题', 'value': '是否带话题'},
                                    {'label': '是否绑定挑战赛', 'value': '是否绑定挑战赛'},
                                    {'label': '是否文案引导', 'value': '是否文案引导'}
                                ],
                                value='视频时长区间'
                            ),
                        ],
                        className='control_block'
                    ),
                    # Refresh button
                    html.Button(id='submit-button', n_clicks=0, children='刷新'),
                    # Debug window
                    html.Div(
                        [
                            html.H6('Debug'),
                            html.Div(id='debugDiv', children='')
                        ],
                        className='control_block',
                        style={'display': 'none'}
                    ),

                ],
                className='container control_container three columns',
            ),

            # statistic
            html.Div(
                [
                    # Title
                    html.Div(
                        [
                            html.H3(id='block_title',
                                    className='twelve columns'),
                            html.P('年轻人热点数据反馈', className='twelve columns')
                        ],
                        className="container title_container"
                    ),

                    # Description
                    html.P('取热点投放期间数据，其中大盘指代全年龄段，而年轻人指24岁或以下群体',
                           className='twelve columns'),

                    # Floor-1
                    html.Div(
                        [
                            # 播放vv
                            dcc.Graph(id="play_vv_bar",
                                      className='floor_card six columns'),
                            # 条均播放vv
                            dcc.Graph(id="play_vv_perfeed_bar",
                                      className='floor_card six columns'),
                        ],
                        className="container floor_container twelve columns"
                    ),

                    # Floor-2
                    # To show link of the clicked-point in scatter
                    html.Div(id="feedLinkDiv",
                             className="link_container three columns"),

                    html.Div(
                        [
                            # 视频数量
                            dcc.Graph(id="feed_count_bar",
                                      className='floor_card four columns'),
                            # vv区间分布
                            dcc.Graph(id="duration_vv_scatter",
                                      className='floor_card eight columns'),
                        ],
                        className="container floor_container twelve columns"
                    ),

                ],
                className="container nine columns"
            ),
        ],
        className='container control_container twelve columns',
    ),

    # 2nd block - consume details
    html.Div(
        [
            # Floor-3 完播率/播放完成度/互动率
            html.Div(
                [
                    # 完播率
                    dcc.Graph(id="complete_ratio_bar",
                              className='floor_card four columns'),
                    # 播放完成度
                    dcc.Graph(id="play_percentage_bar",
                              className='floor_card four columns'),
                    # 互动率
                    dcc.Graph(id="interact_bar",
                              className='floor_card four columns'),
                ],
                className="container floor_container twelve columns"
            ),

            # Floor-4 3s快滑率/5s快滑率/单vv时长
            html.Div(
                [
                    # 3s快滑率
                    dcc.Graph(id="skip_3s_bar",
                              className='floor_card four columns'),
                    # 5s快滑率
                    dcc.Graph(id="skip_5s_bar",
                              className='floor_card four columns'),
                    # 单vv时长
                    dcc.Graph(id="duration_pervv_bar",
                              className='floor_card four columns'),
                ],
                className="container floor_container twelve columns"
            ),
        ],
        className='container control_container twelve columns',
    ),

    # hidden signal value
    html.Div(id='signal', style={'display': 'none'})

],
    className="container app_structure_container twelve columns"
)


# callback functions
# set title
@app.callback(Output('block_title', 'children'), [Input('mode_dropdown', 'value'), Input('dimension_dropdown', 'value')])
def update_title(mode, dimension):
    return "{}-按{}拆解".format(mode, dimension)


# update intermediate selection in json format
@app.callback(Output('signal', 'children'),
              [Input('submit-button', 'n_clicks')],
              [State('mode_dropdown', 'value'), State('dimension_dropdown', 'value')])
def compute_value(n_clicks, mode, dimension):
    return json.dumps((mode, dimension))


# 播放vv
@app.callback(Output('play_vv_bar', 'figure'), [Input('signal', 'children')])
def update_playvv_graph(jsonified_submit_value):
    mode, dimension = json.loads(jsonified_submit_value)
    subDf = getSubDf(mode, dimension)

    playvvDf = subDf.query(
        "variable.str.contains('播放VV') & ~(variable.str.contains('条均'))")
    playvvFig = px.bar(playvvDf,
                       title='总播放VV对比',
                       x=dimension, y='value', color='人群',
                       labels={"value": "统计值"},
                       barmode='group', template='simple_white', color_discrete_sequence=px.colors.sequential.dense)

    playvvFig.update_traces(texttemplate='%{value:.0f}',
                            textposition='outside')
    playvvFig.update_yaxes(showgrid=True)  # the y-axis
    playvvFig.update_layout(
        height=500,
        title=dict(
            x=0.5, xref='paper', font=dict(size=16)),
        font_family="PingFangSC-Light",
        margin=dict(
            l=30, r=30, b=20, t=100),
        # gap between bars of adjacent location coordinates.
        bargap=0.3,
        # gap between bars of the same location coordinate.
        bargroupgap=0,
        hovermode="closest")
    return playvvFig


# 条均播放vv
@app.callback(Output('play_vv_perfeed_bar', 'figure'), [Input('signal', 'children')])
def update_playvvperfeed_graph(jsonified_submit_value):
    mode, dimension = json.loads(jsonified_submit_value)
    subDf = getSubDf(mode, dimension)

    playvv_perfeedDf = subDf.query("variable.str.contains('条均播放VV')")
    playvv_perfeedFig = px.bar(playvv_perfeedDf,
                               title='条均播放VV对比',
                               x=dimension, y='value', color='人群',
                               labels={"value": "统计值"},
                               barmode='group', template='simple_white', color_discrete_sequence=px.colors.sequential.dense)

    playvv_perfeedFig.update_traces(texttemplate='%{value:.0f}',
                                    textposition='outside')
    playvv_perfeedFig.update_yaxes(showgrid=True)  # the y-axis
    playvv_perfeedFig.update_layout(
        height=500,
        title=dict(
            x=0.5, xref='paper', font=dict(size=16)),
        font_family="PingFangSC-Light",
        margin=dict(
            l=30, r=30, b=20, t=100),
        # gap between bars of adjacent location coordinates.
        bargap=0.3,
        # gap between bars of the same location coordinate.
        bargroupgap=0,
        hovermode="closest")
    return playvv_perfeedFig


# 视频数量
@app.callback(Output('feed_count_bar', 'figure'), [Input('signal', 'children')])
def update_feedcount_graph(jsonified_submit_value):
    mode, dimension = json.loads(jsonified_submit_value)
    subDf = getSubDf(mode, dimension)

    feedcountDf = subDf.query("variable.str.contains('视频数量')")
    feedcountFig = px.pie(feedcountDf, values='value', names=dimension,
                          title='视频数量对比',
                          template='simple_white',
                          color_discrete_sequence=px.colors.sequential.dense)

    feedcountFig.update_traces(textposition='inside',
                               textinfo='percent+label+value',
                               hole=0.3, pull=[0.05, 0.05, 0.05, 0.05, 0, 0, 0])

    feedcountFig.update_layout(
        height=500,
        title=dict(
            x=0.5, xref='paper', font=dict(size=16)),
        font_family="PingFangSC-Light",
        margin=dict(
            l=30, r=30, b=20, t=100),
        hovermode="closest",
        uniformtext_minsize=12, uniformtext_mode='hide', showlegend=True)

    return feedcountFig


# 时长-vv散点图
@app.callback(Output('duration_vv_scatter', 'figure'), [Input('signal', 'children')])
def update_duration_vv_scatter_graph(jsonified_submit_value):
    mode, dimension = json.loads(jsonified_submit_value)
    duration_vv_subDf = getSubDf_byduration(mode, dimension)

    duration_vv_Fig = px.scatter(duration_vv_subDf,
                                 title='视频时长-播放vv散点图',
                                 x='视频时长', y='value', color=dimension, facet_col='人群', hover_data=[dimension, '视频id'],
                                 labels={"value": "播放vv"},
                                 template='simple_white', color_discrete_sequence=px.colors.sequential.Rainbow)

    duration_vv_Fig.update_yaxes(showgrid=True)  # the y-axis
    duration_vv_Fig.update_layout(
        height=500,
        title=dict(
            x=0.5, xref='paper', font=dict(size=16)),
        font_family="PingFangSC-Light",
        margin=dict(
            l=30, r=30, b=20, t=100),
        hovermode="closest")
    return duration_vv_Fig


# 散点图点击事件
@app.callback(
    Output('feedLinkDiv', 'children'),
    [Input('duration_vv_scatter', 'clickData')])
def display_duration_vv_scatter_click_data(clickData):
    if (clickData is None):
        return ""

    dimension = clickData['points'][0]['customdata'][0]
    video_id = clickData['points'][0]['customdata'][1]
    vv = clickData['points'][0]['y']

    return html.Div(
        [
            html.P("{}, {}  ".format(dimension, vv)),
            html.A(
                video_id, href="https://h5.weishi.qq.com/weishi/feed/{}".format(video_id), target='_blank')
        ],
        className="link_item")


# 完播率
@app.callback(Output('complete_ratio_bar', 'figure'), [Input('signal', 'children')])
def update_complete_ratio_graph(jsonified_submit_value):
    mode, dimension = json.loads(jsonified_submit_value)
    subDf = getSubDf(mode, dimension)

    complete_ratioDf = subDf.query("variable.str.contains('完播率')")
    complete_ratioFig = px.bar(complete_ratioDf,
                               title='完播率对比',
                               x=dimension, y='value', color='人群', facet_row='统计方式', facet_row_spacing=0.05,
                               labels={"value": "统计值"},
                               barmode='group', template='simple_white', color_discrete_sequence=px.colors.sequential.Bluyl)

    complete_ratioFig.update_traces(texttemplate='%{value:.2f}',
                                    textposition='outside')
    complete_ratioFig.update_yaxes(
        range=[0, 0.3], showgrid=True)  # the y-axis
    complete_ratioFig.update_layout(
        height=900,
        title=dict(
            x=0.5, xref='paper', font=dict(size=16)),
        font_family="PingFangSC-Light",
        margin=dict(
            l=30, r=30, b=20, t=100),
        # gap between bars of adjacent location coordinates.
        bargap=0.3,
        # gap between bars of the same location coordinate.
        bargroupgap=0,
        hovermode="closest")
    return complete_ratioFig


# 播放完成度
@app.callback(Output('play_percentage_bar', 'figure'), [Input('signal', 'children')])
def update_play_percentage_graph(jsonified_submit_value):
    mode, dimension = json.loads(jsonified_submit_value)
    subDf = getSubDf(mode, dimension)

    play_percentageDf = subDf.query("variable.str.contains('播放完成度')")
    play_percentageFig = px.bar(play_percentageDf,
                                title='播放完成度对比',
                                x=dimension, y='value', color='人群', facet_row='统计方式', facet_row_spacing=0.05,
                                labels={"value": "统计值"},
                                barmode='group', template='simple_white', color_discrete_sequence=px.colors.sequential.Bluyl)

    play_percentageFig.update_traces(texttemplate='%{value:.2f}',
                                     textposition='outside')
    play_percentageFig.update_yaxes(
        range=[0, 0.6], showgrid=True)  # the y-axis
    play_percentageFig.update_layout(
        height=900,
        title=dict(
            x=0.5, xref='paper', font=dict(size=16)),
        font_family="PingFangSC-Light",
        margin=dict(
            l=30, r=30, b=20, t=100),
        # gap between bars of adjacent location coordinates.
        bargap=0.3,
        # gap between bars of the same location coordinate.
        bargroupgap=0,
        hovermode="closest")
    return play_percentageFig


# 互动率
@app.callback(Output('interact_bar', 'figure'), [Input('signal', 'children')])
def update_playvv_graph(jsonified_submit_value):
    mode, dimension = json.loads(jsonified_submit_value)
    subDf = getSubDf(mode, dimension)

    interactDf = subDf.query("variable.str.contains('互动率')")
    interactFig = px.bar(interactDf,
                         title='互动率对比',
                         x=dimension, y='value', color='人群', facet_row='统计方式', facet_row_spacing=0.05,
                         labels={"value": "统计值"},
                         barmode='group', template='simple_white', color_discrete_sequence=px.colors.sequential.Blugrn)

    interactFig.update_traces(texttemplate='%{value:.3f}',
                              textposition='outside')
    interactFig.update_yaxes(
        range=[-0.01, 0.01], showgrid=True)  # the y-axis
    interactFig.update_layout(
        height=900,
        title=dict(
            x=0.5, xref='paper', font=dict(size=16)),
        font_family="PingFangSC-Light",
        margin=dict(
            l=30, r=30, b=20, t=100),
        # gap between bars of adjacent location coordinates.
        bargap=0.3,
        # gap between bars of the same location coordinate.
        bargroupgap=0,
        hovermode="closest")
    return interactFig


# 3s快滑率
@app.callback(Output('skip_3s_bar', 'figure'), [Input('signal', 'children')])
def update_skip_3s_graph(jsonified_submit_value):
    mode, dimension = json.loads(jsonified_submit_value)
    subDf = getSubDf(mode, dimension)

    skip_3sDf = subDf.query("variable.str.contains('3s快滑率')")
    skip_3sFig = px.bar(skip_3sDf,
                        title='3s快滑率对比',
                        x=dimension, y='value', color='人群', facet_row='统计方式', facet_row_spacing=0.05,
                        labels={"value": "统计值"},
                        barmode='group', template='simple_white', color_discrete_sequence=px.colors.sequential.Blugrn)

    skip_3sFig.update_traces(texttemplate='%{value:.2f}',
                             textposition='outside')
    skip_3sFig.update_yaxes(
        range=[0, 0.8], showgrid=True)  # the y-axis
    skip_3sFig.update_layout(
        height=900,
        title=dict(
            x=0.5, xref='paper', font=dict(size=16)),
        font_family="PingFangSC-Light",
        margin=dict(
            l=30, r=30, b=20, t=100),
        # gap between bars of adjacent location coordinates.
        bargap=0.3,
        # gap between bars of the same location coordinate.
        bargroupgap=0,
        hovermode="closest")
    return skip_3sFig


# 5s快滑率
@app.callback(Output('skip_5s_bar', 'figure'), [Input('signal', 'children')])
def update_skip_5s_graph(jsonified_submit_value):
    mode, dimension = json.loads(jsonified_submit_value)
    subDf = getSubDf(mode, dimension)

    skip_5sDf = subDf.query("variable.str.contains('5s快滑率')")
    skip_5sFig = px.bar(skip_5sDf,
                        title='5s快滑率对比',
                        x=dimension, y='value', color='人群', facet_row='统计方式', facet_row_spacing=0.05,
                        labels={"value": "统计值"},
                        barmode='group', template='simple_white', color_discrete_sequence=px.colors.sequential.Blugrn)

    skip_5sFig.update_traces(texttemplate='%{value:.2f}',
                             textposition='outside')
    skip_5sFig.update_yaxes(
        range=[0, 0.8], showgrid=True)  # the y-axis
    skip_5sFig.update_layout(
        height=900,
        title=dict(
            x=0.5, xref='paper', font=dict(size=16)),
        font_family="PingFangSC-Light",
        margin=dict(
            l=30, r=30, b=20, t=100),
        # gap between bars of adjacent location coordinates.
        bargap=0.3,
        # gap between bars of the same location coordinate.
        bargroupgap=0,
        hovermode="closest")
    return skip_5sFig


# 单vv时长
@app.callback(Output('duration_pervv_bar', 'figure'), [Input('signal', 'children')])
def update_playvv_graph(jsonified_submit_value):
    mode, dimension = json.loads(jsonified_submit_value)
    subDf = getSubDf(mode, dimension)

    duration_pervvDf = subDf.query("variable.str.contains('单vv时长')")
    duration_pervvFig = px.bar(duration_pervvDf,
                               title='单vv时长对比',
                               x=dimension, y='value', color='人群', facet_row='统计方式', facet_row_spacing=0.05,
                               labels={"value": "统计值"},
                               barmode='group', template='simple_white', color_discrete_sequence=px.colors.sequential.Blugrn)

    duration_pervvFig.update_traces(texttemplate='%{value:.2f}',
                                    textposition='outside')
    duration_pervvFig.update_yaxes(range=[0, 10], showgrid=True)  # the y-axis
    duration_pervvFig.update_layout(
        height=900,
        title=dict(
            x=0.5, xref='paper', font=dict(size=16)),
        font_family="PingFangSC-Light",
        margin=dict(
            l=30, r=30, b=20, t=100),
        # gap between bars of adjacent location coordinates.
        bargap=0.3,
        # gap between bars of the same location coordinate.
        bargroupgap=0,
        hovermode="closest")
    return duration_pervvFig


# 完播率/播放完成度/3s快滑率/5s快滑率
# @app.callback(Output('consumestat_bar', 'figure'), [Input('signal', 'children')])
# def update_playvv_graph(jsonified_submit_value):
#     mode, dimension = json.loads(jsonified_submit_value)
#     subDf = getSubDf(mode, dimension)

#     consumeStatDf = subDf.query(
#         "~(variable.str.contains('播放VV') or variable.str.contains('单vv时长') or variable.str.contains('互动率') or variable.str.contains('视频数量'))")
#     consumeStatFig = px.bar(consumeStatDf,
#                             title='完播率/播放完成度/快滑指标对比',
#                             x=dimension, y='value', color='人群', facet_row='统计方式', facet_col='指标', facet_row_spacing=0.05, facet_col_spacing=0.03,
#                             labels={"value": "统计值"},
#                             barmode='group', template='simple_white', color_discrete_sequence=px.colors.qualitative.Pastel1)

#     consumeStatFig.update_traces(texttemplate='%{value:%.2f}',
#                                  textposition='outside')
#     consumeStatFig.update_yaxes(showgrid=True)  # the y-axis
#     consumeStatFig.update_layout(
#         height=900,
#         title=dict(
#             x=0.5, xref='paper', font=dict(size=16)),
#         font_family="PingFangSC-Light",
#         margin=dict(
#             l=30, r=30, b=20, t=100),
#         # gap between bars of adjacent location coordinates.
#         bargap=0.3,
#         # gap between bars of the same location coordinate.
#         bargroupgap=0,
#         hovermode="closest")
#     return consumeStatFig
