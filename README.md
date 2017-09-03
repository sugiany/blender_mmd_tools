mmd_tools
===========

# Notice: This version is no longer maintained.  Maintained version: https://github.com/powroupi/blender_mmd_tools

概要
----
mmd_toolsはblender用MMD(MikuMikuDance)モデルデータ(.pmd, .pmx)およびモーションデータ(.vmd)インポータです。

### 環境

#### 対応バージョン
blender 2.67以降

#### 動作確認環境
Windows 7 + blender 2.67 64bit


注意
----

現在のmasterブランチは、v0.5.0向け開発バージョンです。

旧バージョンv0.4系列のバグ修正等はメンテナンスブランチ [0.4-main](https://github.com/sugiany/blender_mmd_tools/tree/0.4-main) で行います。

また、UIや使用方法が変わっているため、注意してください。


使用方法
---------
### ダウンロード

* mmd_toolsはGitHubで公開しています。
    * https://github.com/sugiany/blender_mmd_tools
* 安定版は下記リンクから最新版をダウンロードしてください。
    * [Tags](https://github.com/sugiany/blender_mmd_tools/tags)
* 開発版はmasterブランチのHEADを取得してください。基本的に動作確認済みです。
    * [master.zip](https://github.com/sugiany/blender_mmd_tools/archive/master.zip)

### インストール
展開したアーカイブ内のmmd_toolsディレクトリをaddonディレクトリにコピーしてください。

    .../blender-2.67-windows64/2.67/scripts/addons/

### Addonのロード
1. User PrefernceのAddonsから"Object: mmd_tools"探してチェックを入れてください。
   (検索ボックスにmmdと入力すると簡単に探せます。)
2. 3D View左のパネルにMMD Toolsのパネルが表示されます。

### MMDモデルデータ読み込み
1. _Object_ パネルの"Model/Import"ボタンを選択してください。
2. ファイル選択画面でpmxファイルを選択すると、選択されたモデルをインポートします。

### モーションデータの読み込み
1. MMDモデルを読み込み、モデルのメッシュ等を選択してください。
2. _MMD Model Tools_ パネル内の _Import Motion_ ボタンを押下してください。
3. 剛体シミュレーションが必要な場合は、 同パネル内の _Build_ ボタンを押下してください。


各種機能詳細
-------------------------------
### Import Model
MMDモデルデータをインポートします。対応形式はpmdファイルおよびpmx(ver2.0)ファイルです。
各オプションはデフォルト推薦です。
剛体情報を読み込みたくない場合は、"import only non dynamics rigid bodies"オプションをオンにしてください。

* scale
    * スケールです。Import Motion時のスケールと統一してください。
* rename bones
    * ボーンの名前をblenderに適した名前にリネームします。（右腕→腕.Lなど）
* hide rigid bodies and joints
    *  剛体情報を持つ各種オブジェクトを非表示にします。
* import only non dynamics rigid bodies
    * ボーン追従の剛体のみインポートします。clothやsoft bodyを使用する等、剛体情報が不要な場合に使用してください。
* ignore non collision groups
    * 非衝突グループを読み込みません。モデルの読み込み時にフリーズしてしまう場合に使用してください。
* distance of ignore collisions
    * 非衝突グループの解決範囲を指定します。
* use MIP map for UV textures
    * Blenderの自動ミップマップ生成機能のオンオフを指定します。
    * 一部アルファチャンネルを持つテクスチャで紫色のノイズが発生する場合はオフにしてください。
* influence of .sph textures
    * スフィアマップの強度を指定します。(0.0～1.0)
* influence of .spa textures
    * スフィアマップの強度を指定します。(0.0～1.0)

### Import Motion
現在選択中のArmature、MeshおよびCameraにvmdファイルのモーションを適用します。

* scale
    * スケールです。Import Model時のスケールと統一してください。
* margin
    * 物理シミュレーション用の余白フレームです。
    * モーションの初期位置が原点から大きく離れている場合、モーション開始時にモデルが瞬間移動してしまうため物理シミュレーションが破綻します。
    この現象を回避するため、blenderのタイムライン開始とモーション開始の間に余白を挿入します。
    * モーション開始時に剛体を安定させる効果もあります。
* update scene settings
    * モーションデータ読み込み後にフレームレンジおよびフレームレートの自動設定を行います。
    * フレームレンジは現在シーン中に存在するアニメーションを全て再生するために必要なレンジを設定します。
    * フレームレートを30fpsに変更します。

### Set frame range
フレームレンジは現在シーン中に存在するアニメーションを全て再生するために必要なレンジを設定します。
また、フレームレートを30fpsに変更します。
* Import vmdのupdate scene settingsオプションと同じ機能です。

### View

#### GLSL
GLSLモードで表示するための必要設定を自動で行います。
* ShadingをGLSLに切り替えます。
* 現在のシーン内全てのマテリアルのshadelessをオフにします。
* Hemiライトを追加します。
* ボタンを押した3DViewのシェーディングをTexturedに変更します。

#### Shadeless
Shadelessモードで表示するための必要設定を自動で行います。
* ShadingをGLSLに切り替えます。
* 現在のシーン内全てのマテリアルをshadelessにします。
* ボタンを押した3DViewのシェーディングをTexturedに変更します。

#### Cycles
シーン内に存在する全てのマテリアルをCycles用に変換します。
* 何の根拠もない適当な変換です。
* 完了メッセージなどは表示されません。マテリアルパネルから変換されているかどうか確認してください。
* ボタンを押した3DViewのシェーディングをMaterialに変更します。
    * 3DViewのシェーディングをRenderedに変更すれば、Cyclesのリアルタイムプレビューが可能です。
* ライティングは変更しません。設定が面倒な場合は、WorldのColorを白(1,1,1)に変更すればそれなりに見えます。

#### Reset
GLSLボタンで変更した内容を初期状態に戻します。

#### Separate by materials
選択したメッシュオブジェクトのメッシュをマテリアル毎に分割し、分割後のオブジェクト名を各マテリアル名に変更します。
* blenderデフォルトの"Separate"→"By Material"機能を使用しています。


その他
------
* カメラとキャラクタモーションが別ファイルの場合は、ArmatureとMeshを選択してキャラモーション、Cameraを選択してカメラモーションというように2回に分けてインポートしてください。
* モーションデータのインポート時はボーン名を利用して各ボーンにモーションを適用します。
    * ボーン名と構造がMMDモデルと一致していれば、オリジナルのモデル等にもモーションのインポートが可能です。
    * mmd_tools以外の方法によってMMDモデルを読み込む場合、ボーン名をMMDモデルと一致させてください。
* カメラはMMD_Cameraという名前のEmptyオブジェクトを生成し、このオブジェクトにモーションをアサインします。
* 複数のモーションをインポートする場合やフレームにオフセットをつけてインポートしたい場合は、NLAエディタでアニメーションを編集してください。
* アニメーションの初期位置がモデルの原点と大きく離れている場合、剛体シミュレーションが破綻することがあります。その際は、vmdインポートパラメータ"margin"を大きくしてください。
* モーションデータは物理シミュレーションの破綻を防止するため"余白"が追加されます。この余白はvmdインポート時に指定する"margin"の値です。
    * インポートしたモーション本体は"margin"の値+1フレーム目から開始されます。（例：margin=5の場合、6フレーム目がvmdモーションの0フレーム目になります）
* pmxインポートについて
    * 頂点のウェイト情報がSDEFの場合、BDEF2と同じ扱いを行います。
    * 頂点モーフ以外のモーフ情報には対応していません。
    * 剛体設定の"物理+ボーン位置合わせ"は"物理演算"として扱います。
* 複数のpmxファイルをインポートする場合はscaleを統一してください。


既知の問題
----------
* 剛体の非衝突グループを強引に解決しているため、剛体の数が多いモデルを読み込むとフリーズすることがあります。
    * 正確には完全なフリーズではなく、読み込みに異常な時間がかかっているだけです。
    * フリーズするモデルを読み込む場合は、"ignore non collision groups"オプションにチェックを入れてください。
    * 上記オプションをオンにした場合、意図しない剛体同士が干渉し、正常に物理シミュレーションが動作しない可能性があります。
* 「移動付与」ボーンは正常に動作しません。
* オブジェクトの座標（rootのemptyおよびArmature）を原点から移動させると、ボーン構造が破綻することがあります。
    * モデルを移動させたい場合は、オブジェクトモードでの移動は行わず、Pose Modeで「センター」や「全ての親」などのボーンを移動させてください。
    * 現状、解決が難しいため、オブジェクトモードでの移動操作は行わないことをおすすめします。


バグ・要望・質問等
------------------
GitHubのIssueに登録するか、twitterでどうぞ。  
[@sugiany](https://twitter.com/sugiany)


変更履歴
--------
CHANGELOG.mdを参照してください。


ライセンス
----------
&copy; 2012-2014 sugiany  
Distributed under the MIT License.  
